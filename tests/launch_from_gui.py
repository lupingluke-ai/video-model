# Run from Blender's Python console:
#   exec(open('/Users/user/Documents/personal/video-model/tests/launch_from_gui.py').read())
# Starts a separate HEADLESS Blender (blender -b) that runs tests/bench.py, so the GUI stays
# responsive. Progress: tests/results/bench_progress.txt
import bpy, subprocess, os
here = os.path.expanduser("~/Documents/personal/video-model/tests")
os.makedirs(os.path.join(here, "results"), exist_ok=True)
logf = open(os.path.join(here, "results", "cli_stdout.log"), "w")
cmd = [bpy.app.binary_path, "-b", "--factory-startup", "-P", os.path.join(here, "bench.py")]
subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT)
print("started:", cmd)
