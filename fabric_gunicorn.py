from time import sleep

from fabric import colors
from fabric.api import task, env, run, cd
from fabric.utils import abort, puts
from fabric.contrib import files

def set_env_defaults():
    env.setdefault('remote_workdir', '~')
    env.setdefault('gunicorn_pidpath', env.remote_workdir + '/gunicorn.pid')
    env.setdefault('gunicorn_bind', '127.0.0.1:8000')
    
set_env_defaults()

def gunicorn_running():
    return files.exists(env.gunicorn_pidpath)

@task
def status():
    set_env_defaults()
    if gunicorn_running():
        puts(colors.green("gunicorn is running"))
    else:
        puts(colors.blue("gunicorn isn't running"))

@task
def start():
    set_env_defaults()
    if gunicorn_running():
        puts(colors.red("gunicorn is allready running"))
        return
    
    if 'gunicorn_wsgi_app' not in env:
        abort(colors.red('env.gunicorn_wsgi_app not defined'))
        
    with cd(env.remote_workdir):
        prefix = []
        if 'virtualenv_dir' in env:
            prefix.append('source %s/bin/activate' % env.virtualenv_dir)
        if 'django_settings_module' in env:
            prefix.append('export DJANGO_SETTINGS_MODULE=%s' % 
                          env.django_settings_module)
        
        prefix_string = ' && '.join(prefix)
        if len(prefix_string) > 0:
            prefix_string += ' && '
        
        options = [
            '--daemon',
            '--pid %s' % env.gunicorn_pidpath,
            '--bind %s' % env.gunicorn_bind,
        ]
        options_string = ' '.join(options)
        
        run('%sgunicorn %s %s' % (prefix_string, options_string, 
                                  env.gunicorn_wsgi_app))

        if gunicorn_running():
            puts(colors.green("gunicorn started"))
        else:
            abort(colors.red("gunicorn doesn't started"))

@task
def stop():
    set_env_defaults()
    if not gunicorn_running():
        puts(colors.red("gunicorn doesn't running"))
        return
    
    run('kill `cat %s`' % (env.gunicorn_pidpath))

    for i in range(0, 5):
        puts('.', end='', show_prefix=i==0)
        
        if gunicorn_running():
            sleep(1)
        else:
            puts('', show_prefix=False)
            puts(colors.green("gunicorn stopped"))
            break
    else:
        puts(colors.red("gunicorn doesn't stopped"))
        return            
            