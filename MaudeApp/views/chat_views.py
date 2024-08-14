from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.conf import settings
import os
from ..models import Session, Command
import pexpect
import tempfile

class SessionListView(ListView):
    model = Session
    template_name = 'chat/session_list.html'
    context_object_name = 'sessions'

class SessionDetailView(DetailView):
    model = Session
    template_name = 'chat/session_detail.html'
    context_object_name = 'session'
 
class CommandCreateView(View):
    def post(self, request, *args, **kwargs):
        session = get_object_or_404(Session, id=kwargs['session_id'])
        input_text = request.POST.get('input_text')

        if input_text:
            # Save the command to the database
            command = Command(session=session, input_text=input_text)
            command.save()

            # Execute the Maude command
            output_text = self.execute_maude_command(session, input_text)
            
            # Update the command with the output
            command.output_text = output_text
            command.save()

            # Return the response as JSON
            return JsonResponse({'input_text': input_text, 'output_text': output_text})

        return JsonResponse({'error': 'No input_text provided'}, status=400)

    def execute_maude_command(self, session, input_text):
        # Example implementation of executing a Maude command
        # Append the command to the session's .maude file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.maude', delete=False) as f:
            # Write previous commands to the file
            for command in session.commands.all():
                f.write(command.input_text + '\n')
            # Write the new command
            f.write(input_text + '\n')
            f.flush()

            # Execute the Maude interpreter
            child = pexpect.spawn(f'maude {f.name}')
            child.expect(pexpect.EOF)
            output = child.before.decode('utf-8')
        
        return output

def add_message(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.method == 'POST':
        input_text = request.POST.get('input_text')

        if input_text:
            # Save the command to the database
            command = Command(session=session, input_text=input_text)
            command.save()

            # Execute the Maude command
            output_text = execute_maude_command(session, input_text)

            # Update the command with the output
            command.output_text = output_text
            command.save()

            # Return the response as JSON
            return JsonResponse({'input_text': input_text, 'output_text': output_text})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def post_execute_new_command(request):
    if request.method == 'POST':
        user = request.user
        session_id = request.POST["session"]
        session = get_object_or_404(Session, id=session_id)
        command_text = request.POST["command"]

        # Save the command to the database
        command = Command(session=session, input_text=command_text)
        command.save()
        # Define the path to the .maude file for this session
        maude_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session_id}.maude")

        response = executeMaudeCommand(maude_file_path, command_text)

        command.output_text = response
        command.save()
        
        # Append the new command to the .maude file
        with open(maude_file_path, 'a') as maude_file:
            maude_file.write(command_text + '\n')

        return JsonResponse({
        "hey": response
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Additional views for session management
def start_new_session(request):
    if request.method == 'POST':
        user = request.user
        session = Session.objects.create(user=user)
        # Obtener la ruta del archivo .maude
        maude_file_path = os.path.join(settings.MAUDE_FILES_DIR, f"{session.id}.maude")
        # Crear la carpeta si no existe
        if not os.path.exists(settings.MAUDE_FILES_DIR):
            os.makedirs(settings.MAUDE_FILES_DIR)
        # Crear el archivo vacío
        with open(maude_file_path, 'w') as maude_file:
            pass  # Crear el archivo vacío

        # Continuar con el resto de la lógica
        return JsonResponse({
        "session_id": session.id
        })

def executeMaudeCommand(previous_file, new_command):
    p = pexpect.spawnu(f'{settings.MAUDE_EXECUTABLE_PATH} -no-banner -allow-files', encoding='utf-8')
    p.expect("Maude>")
    p.sendline("load ./bin/borrarluego/list \n")
    p.sendline(f"load {settings.CITP_EXECUTABLE_PATH} \n")
    p.expect("CITP >")
    p.sendline(f"load {previous_file} \n")
    p.expect("CITP >")
    p.sendline(new_command)
    p.expect("CITP >")
    print(p.before)
    return p.before