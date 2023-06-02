import subprocess
from urllib.parse import quote
from urllib.request import urlretrieve
from tempfile import mkdtemp
import os
import glob
import shutil
import platform
import argparse


jre_modules = 'java.base,java.datatransfer,java.desktop,java.logging,java.security.sasl,java.xml,jdk.crypto.ec,jdk.jdwp.agent'


def build_jre(jre_dir):
    process = subprocess.Popen(['jlink',
                                '--compress', '0',
                                '--strip-debug',
                                '--no-header-files',
                                '--no-man-pages',
                                '--add-modules',
                                jre_modules,
                                '--output', jre_dir
                                ],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr:
        raise Exception(stderr)
    return stdout


def build_win_package(name, app_version):
    add_opts = [
        '--win-shortcut-prompt',
        '--win-dir-chooser',
        '--win-menu',
        '--win-menu-group', name,
    ]
    if os.path.exists('icon.ico'):
        add_opts = add_opts + ['--icon', 'icon.ico']
    return build_package(package_type='exe', name=name, app_version=app_version, additional_opts=add_opts)


def fun():
    print("""
    define fun!
    """)


def fun():
    print("define fun!")


def fun():
    print('''
    define fun!
    ''')

def build_mac_package(name, app_version):
    return build_package(package_type='pkg', name=name, app_version=app_version,
                         additional_opts=['--mac-package-identifier', 'ShutterEncoder'])


def build_package(package_type, name, app_version, additional_opts):
    process = subprocess.Popen(['jpackage',
                                '--type', package_type,
                                '--name', name,
                                '--runtime-image', 'JRE',
                                '--resource-dir', 'Library',
                                '--resource-dir', 'Languages',
                                '--input', '.',
                                '--main-jar', 'Shutter Encoder.jar',
                                '--license-file', 'LICENCE.txt',
                                '--app-version', app_version,
                                ] + additional_opts,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if stderr:
        raise Exception(stderr)
    return stdout


def create_icon(icon_to_convert, output_icon_dir):
    process = subprocess.Popen(['convert',
                                '-background',
                                'transparent',
                                icon_to_convert,
                                os.path.join(output_icon_dir, 'icon.ico')
                                ])
    stdout, stderr = process.communicate()
    if stderr:
        raise Exception(stderr)
    return stdout


win_package_name = "Shutter Encoder 16.8 Windows 64bits"


def download_shutter_encoder_package():
    url = "https://www.shutterencoder.com/" + quote(win_package_name + ".zip")
    temp_dir = mkdtemp()
    print("Downloading zip from " + url + " to " + temp_dir)
    filename, _ = urlretrieve(url, os.path.join(temp_dir, "shutterencoder.zip"))
    shutil.unpack_archive(filename, temp_dir)
    return os.path.join(temp_dir, win_package_name)


parser = argparse.ArgumentParser(
    prog='Shutter Encoder build script',
    description='Build installable package for Shutter Encoder',
    epilog='This is a simple build script for Shutter Encoder')
parser.add_argument('-n', '--name', default='Shutter Encoder')
parser.add_argument('-v', '--app-version', default='1.0.0')
parser.add_argument('-i', '--icon-file')
args = parser.parse_args()
current_dir = os.curdir
output_dir = os.path.join(current_dir, "out")
if not os.path.exists(output_dir):
    os.mkdir(output_dir)
custom_jre_dir = os.path.join(output_dir, "JRE")
if not os.path.exists(custom_jre_dir):
    build_jre(custom_jre_dir)
# copy fonts to JRE
jre_fonts_dir = os.path.join(custom_jre_dir, "lib", "fonts")
if not os.path.exists(jre_fonts_dir):
    shutil.copytree(os.path.join(current_dir, "fonts"), jre_fonts_dir)
# copy Library
output_lib_dir = os.path.join(output_dir, "Library")
if not os.path.exists(output_lib_dir):
    se_package_dir = download_shutter_encoder_package()
    shutil.copytree(os.path.join(se_package_dir, "Library"), output_lib_dir)
# copy Languages
output_lang_dir = os.path.join(output_dir, "Languages")
if not os.path.exists(output_lang_dir):
    shutil.copytree(os.path.join(current_dir, "Languages"), output_lang_dir)
# copy "Shutter Encoder.jar"
output_jar_filename = os.path.join(output_dir, "Shutter Encoder.jar")
shutil.copyfile(os.path.join(current_dir, "Shutter Encoder.jar"), output_jar_filename)
# copy LICENCE.txt
output_licence_filename = os.path.join(output_dir, "LICENCE.txt")
if not os.path.exists(output_licence_filename):
    shutil.copyfile(os.path.join(current_dir, "LICENCE.txt"), output_licence_filename)
# create or copy icon.ico
contents_dir = os.path.join(current_dir, "src", "contents")
output_icon_filename = os.path.join(output_dir, "icon.ico")
if not os.path.exists(output_icon_filename):
    if args.icon_file and os.path.exists(args.icon_file):
        print('icon file ' + args.icon_file + ' was passed as an argument')
        shutil.copyfile(args.icon_file, output_icon_filename)
    elif shutil.which('magick'):
        print('icon not passed as arg, but imagemagick detected')
        icon_png_filename = os.path.join(contents_dir, "icon.png")
        create_icon(icon_png_filename, output_dir)
    else:
        print("icon not found. Please install imagemagick or create .ico manually and put it to '" + output_dir + "'.")
os.chdir(output_dir)
system_name = platform.system()
if system_name == "Windows":
    for file in glob.glob("*.exe"):
        os.remove(file)
    build_win_package(args.name, args.app_version)
elif system_name == "Darwin":
    for file in glob.glob("*.pkg"):
        os.remove(file)
    build_mac_package(args.name, args.app_version)
else:
    print(system_name + " not supported")
