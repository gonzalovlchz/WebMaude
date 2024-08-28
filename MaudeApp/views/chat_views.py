from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView
from django.conf import settings
from ansi2html import Ansi2HTMLConverter
import os
from ..models import Session, Command
import pexpect
import tempfile
import json

@login_required 
def get_chat_session(request):
    if request.method == 'GET':
        session_id = request.GET["session"]
        session = get_object_or_404(Session, id=session_id)

        commands = session.commands.all()

        # Serialize commands to a list of dictionaries
        conv = Ansi2HTMLConverter()
        commands_list = [
            {
                "id": command.id,
                "input_text": command.input_text,
                "output_text": conv.convert(command.output_text),
                "timestamp": command.timestamp,
            }
            for command in commands
        ]

        return JsonResponse({"commands": commands_list})


@login_required    
def get_all_sessions(request):
    if request.method == 'GET':
        # Get all sessions for the current user
        sessions = Session.objects.filter(user=request.user).values('id', 'created_at', 'updated_at', 'file_path')

        # Convert the queryset to a list to return as JSON
        sessions_list = list(sessions)

        return JsonResponse({'sessions': sessions_list})



def post_execute_new_command(request):
    if request.method == 'POST':
        
        session_id = request.POST["session"]
        session = get_object_or_404(Session, id=session_id)

        file_extension = ".cafe" if session.session_type == "cafeInMaude" else ".maude"

        # Define the path to the .maude file for this session
        maude_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session_id}/{session_id}{file_extension}")
        
        for file in request.FILES.getlist('file[]'):
            with open(maude_file_path, 'ab') as dest:
                if file.multiple_chunks():
                    for chunk in file.chunks():
                        dest.write(chunk)
                else:
                    dest.write(file.read())

        
        command_text = request.POST["command"]


        # Save the command to the database
        command = Command(session=session, input_text=command_text)
        command.save()
        
        # Define the path to the .maude file for this session
        if session.session_type == "cafeInMaude":
            cafe_in_maude_option = request.POST.get("cafeInMaudeOption")
            if cafe_in_maude_option is not "examples":
                maude_previous_file_path = cafe_in_maude_option
            else:
                maude_previous_file_path = None
        else:
            maude_previous_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session.id}/previous{file_extension}")

        # Execute command based on session type
        if session.session_type == 'CITP':
            response = executeCITPCommand(maude_previous_file_path, maude_file_path, command_text)
        else:
            response = executeCafeInMaudeCommand(maude_previous_file_path, maude_file_path, command_text)

        command.output_text = response
        command.save()
        
        # Append the new command to the .maude file
        with open(maude_file_path, 'a') as maude_file:
            maude_file.write(command_text + '\n')

        conv = Ansi2HTMLConverter()
        return JsonResponse({
        "output": conv.convert(response)
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Additional views for session management
@login_required
def start_new_session(request):
    if request.method == 'POST':
        user = request.user
        session_type = request.POST.get("sessionType", "cafeInMaude")
        session = Session.objects.create(user=user, session_type=session_type)
        # Definir la extensión de archivo basada en el tipo de sesión
        file_extension = ".cafe" if session_type == "cafeInMaude" else ".maude"
        # Obtener la ruta del archivo .maude
        maude_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session.id}/{session.id}{file_extension}")
        # Crear la carpeta si no existe
        os.makedirs(os.path.dirname(maude_file_path), exist_ok=True)
        # Crear el archivo vacío
        with open(maude_file_path, 'w') as maude_file:
            pass  # Crear el archivo vacío

        maude_previous_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session.id}/previous{file_extension}")
        # Crear el archivo vacío
        with open(maude_previous_file_path, 'w') as maude_file:
            pass  # Crear el archivo vacío

        for file in request.FILES.getlist('file[]'):
            with open(maude_previous_file_path, 'ab') as dest:
                if file.multiple_chunks():
                    for chunk in file.chunks():
                        dest.write(chunk)
                else:
                    dest.write(file.read())

        # Continuar con el resto de la lógica
        return JsonResponse({
        "session_id": session.id
        })

def executeCITPCommand(previous_maude_file, previous_citp_file, new_command):
    p = pexpect.spawnu(f'{settings.MAUDE_EXECUTABLE_PATH} -no-banner -allow-files', encoding='utf-8')
    p.setecho(False)
    p.delaybeforesend = None
    p.expect("Maude>")
    p.sendline(f"load {previous_maude_file} \n")
    p.sendline(f"load {settings.CITP_EXECUTABLE_PATH} \n")
    # Regular expression to match the three patterns
    citp_pattern = r'CITP(?:/[^ ]*)? >'
    p.expect(citp_pattern)
    p.sendline(f"load {previous_citp_file} \n")
    p.expect(citp_pattern)

    p.sendline(new_command)

    p.expect(citp_pattern)
    output = p.before.strip()
    print(output)
    # Remove the command from the output
    if output.startswith("> "+new_command):
        output = output[len("> "+new_command):].lstrip()
    return output

def executeCafeInMaudeCommand(previous_maude_file, maude_file_path, new_command, timeout=None):
    print("Estoy para mandar el comando de cafe")
    p = pexpect.spawnu(f'{settings.MAUDE_EXECUTABLE_PATH} -allow-files {settings.CAFE_EXECUTABLE_PATH}', encoding='utf-8')
    p.setecho(False)
    p.delaybeforesend = None
    p.expect("CafeInMaude>")

    # Tiempo de espera predeterminado si no se proporciona uno
    if timeout is None:
        timeout = settings.DEFAULT_TIMEOUT

    try:
        if previous_maude_file is not None:
            # Mapeo de archivos a sus rutas
            file_paths = {
                "2p-mutex": "../examples/CCiMPG/2p-mutex/2p-mutex.cafe",
                "abp": "../examples/CCiMPG/ABP/abp.cafe",
                "cloud": "../examples/CCiMPG/Cloud/cloud.cafe",
                "mcs": "../examples/CCiMPG/MCS/mcs.cafe",
                "nslp": "../examples/CCiMPG/NSLP/nslpk.cafe",
                "nslpk2": "../examples/CCiMPG/NSLPK2/nslpk2.cafe",
                "qlock": "../examples/CCiMPG/Qlock/qlock.cafe",
                "scp": "../examples/CCiMPG/SCP/scp.cafe",
                "tas": "../examples/CCiMPG/TAS/tas.cafe"
            }
            # Obtener la ruta del archivo basado en el valor de previous_maude_file
            file_path = file_paths.get(previous_maude_file)

            # Si existe una ruta para ese archivo, enviar el comando
            if file_path:
                p.sendline(f"load {file_path} .")

        p.expect("CafeInMaude>", timeout=timeout)
        p.sendline(f"load {maude_file_path} .")
        p.expect("CafeInMaude>", timeout=timeout)
        aux = p.before.strip()
        p.sendline(new_command)
        p.expect("CafeInMaude>", timeout=timeout)
        output = aux + p.before.strip()
        print(output)
        # Remove the command from the output
        if output.startswith("> "+new_command):
            output = output[len("> "+new_command):].lstrip()
        return output
    
    except pexpect.TIMEOUT:
        print("Timeout esperando respuesta de CafeInMaude")
        return "Error: Timeout esperando respuesta de CafeInMaude"