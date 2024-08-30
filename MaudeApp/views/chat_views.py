from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView
from django.conf import settings
from ansi2html import Ansi2HTMLConverter
import os
from ..models import Session, Command, ExampleFile, SiteSetting
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

        return JsonResponse({"commands": commands_list, "sessionType": session.session_type})


@login_required    
def get_all_sessions(request):
    if request.method == 'GET':
        # Get all sessions for the current user
        sessions = Session.objects.filter(user=request.user).values('id', 'created_at', 'updated_at', 'session_type')

        # Convert the queryset to a list to return as JSON
        sessions_list = list(sessions)

        return JsonResponse({'sessions': sessions_list})

@login_required
def get_files_by_session_type(request):
    if request.method == 'GET':
        # Get the session_type from the query parameters
        session_type = request.GET.get('session_type', None)
        
        if not session_type:
            return JsonResponse({'error': 'session_type parameter is required'}, status=400)

        # Filter ExampleFile objects by session_type
        example_files = ExampleFile.objects.filter(session_type=session_type).values('id', 'name', 'maude', 'program', 'session_type')

        # Convert the queryset to a list to return as JSON
        example_files_list = list(example_files)

        return JsonResponse({'example_files': example_files_list})

def post_execute_new_command(request):
    if request.method == 'POST':
        
        session_id = request.POST["session"]
        session = get_object_or_404(Session, id=session_id)

        maude_previous_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session.id}/previous")

        # Define the path to the .maude file for this session
        maude_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session_id}/{session_id}")

        if 'exampleFile' in request.POST:
            example_file_name = request.POST.get('exampleFile', None)
            # Query the File model to find the file by name
            file_entry = ExampleFile.objects.filter(name=example_file_name).first()
            if not file_entry:
                return JsonResponse({'error': 'File not found'}, status=404)
            # Retrieve file paths and read file contents

            if file_entry.maude:
                maude_content = file_entry.maude.read()
                # Append the contents to the target file
                try:
                    with open(maude_previous_file_path, 'ab') as dest_file:
                        dest_file.write(maude_content)
                except IOError as e:
                    return JsonResponse({'error': f'Error writing to target file: {str(e)}'}, status=500)
                
            if file_entry.program:
                program_content = file_entry.program.read()
                # Append the contents to the target file
                try:
                    with open(maude_file_path, 'ab') as dest_file:
                        dest_file.write(program_content)
                except IOError as e:
                    return JsonResponse({'error': f'Error writing to target file: {str(e)}'}, status=500)

    
        for file in request.FILES.getlist('file[]'):
            with open(maude_file_path, 'ab') as dest:
                if file.multiple_chunks():
                    for chunk in file.chunks():
                        dest.write(chunk)
                else:
                    dest.write(file.read())

        
        if 'command' in request.POST:
            command_text = request.POST["command"]

            # Save the command to the database
            command = Command(session=session, input_text=command_text)
            command.save()

            # Execute command based on session type
            side_command_output=""
            if session.session_type == 'CITP':
                side_command = ""
                if 'side_command' in request.POST:
                    side_command = request.POST["side_command"]

                output, side_command_output = executeCITPCommand(maude_previous_file_path, maude_file_path, command_text, side_command)
            else:
                output = executeCafeInMaudeCommand(maude_file_path, command_text)

            command.output_text = output
            command.save()
            
            # Append the new command to the .maude file
            with open(maude_file_path, 'a') as maude_file:
                maude_file.write(command_text + '\n')

            conv = Ansi2HTMLConverter()
            return JsonResponse({
            "output": conv.convert(output),
            "side_command_output": conv.convert(side_command_output),
            })
        else:
            return True
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Additional views for session management
@login_required
def start_new_session(request):
    if request.method == 'POST':
        user = request.user
        session_type = request.POST.get("sessionType", "cafeInMaude")
        session = Session.objects.create(user=user, session_type=session_type)
        # Obtener la ruta del archivo .maude
        maude_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session.id}/{session.id}")
        # Crear la carpeta si no existe
        os.makedirs(os.path.dirname(maude_file_path), exist_ok=True)
        # Crear el archivo vacío
        with open(maude_file_path, 'w') as maude_file:
            pass  # Crear el archivo vacío

        maude_previous_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session.id}/previous")
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
        "session_id": session.id,
        })

def executeCITPCommand(previous_maude_file, previous_citp_file, new_command, side_command="", timeout=None):
    p = pexpect.spawnu(f'{settings.MAUDE_EXECUTABLE_PATH} -no-banner -allow-files', encoding='utf-8')
    p.setecho(False)
    p.delaybeforesend = None
    p.expect("Maude>")
    # Tiempo de espera predeterminado si no se proporciona uno
    if timeout is None:
        timeout = float(SiteSetting.get_setting('timeout'))
    
    try:
        p.sendline(f"load {previous_maude_file} \n")
        p.sendline(f"load {settings.CITP_EXECUTABLE_PATH} \n")
        # Regular expression to match the three patterns
        citp_pattern = r'CITP(?:/[^ ]*)? >'
        p.expect(citp_pattern, timeout=timeout)
        p.sendline(f"load {previous_citp_file}")
        p.expect(citp_pattern, timeout=timeout)

        p.sendline(new_command)
        p.expect(citp_pattern, timeout=timeout)
        output = p.before.strip()
        print(output)

        output_side = ""
        if side_command!="":
            p.sendline(side_command)    
            p.expect(citp_pattern, timeout=timeout)
            output_side = p.before.strip()

        # Remove the command from the output
        if output.startswith(new_command):
            output = output[len(new_command):].lstrip()
        return output, output_side
    except pexpect.TIMEOUT:
            print("Timeout esperando respuesta de CITP")
            return "Error: Timeout esperando respuesta de CITP", "Error: Timeout esperando respuesta de CITP"

def executeCafeInMaudeCommand(program_file_path, new_command, timeout=None):
    print("Estoy para mandar el comando de cafe")
    p = pexpect.spawnu(f'{settings.MAUDE_EXECUTABLE_PATH} -allow-files {settings.CAFE_EXECUTABLE_PATH}', encoding='utf-8')
    p.setecho(False)
    p.delaybeforesend = None
    p.expect("CafeInMaude>")

    # Tiempo de espera predeterminado si no se proporciona uno
    if timeout is None:
        timeout = float(SiteSetting.get_setting('timeout'))

    try:
        p.sendline(f"load {program_file_path} .")
        p.expect("CafeInMaude>", timeout=timeout)
        p.sendline(new_command)
        p.expect("CafeInMaude>", timeout=timeout)
        output = p.before.strip()
        print(output)
        # Remove the command from the output
        if output.startswith("> "+new_command):
            output = output[len("> "+new_command):].lstrip()
        return output
    
    except pexpect.TIMEOUT:
        print("Timeout esperando respuesta de CafeInMaude")
        return "Error: Timeout esperando respuesta de CafeInMaude"