#!/bin/zsh
# Generic out-of-process Movie Render Queue render (the pattern every Capra and
# TrailGoat render uses). Copy it next to the project's scripts and adapt, or
# call it with arguments:
#
#   render_mrq.sh <project.uproject> <map> <queue asset path> <frames dir> <last frame file> [keep N] [extra args…]
#   render_mrq.sh "/Volumes/KB SS/Unreal Projects/CapraSpace/CassiniSample.uproject" /Game/Levels/Demo \
#       /Game/Capra/Seq/Q_CapraSpace_720 "/Volumes/KB SS/Capra Studios/Unreal/CapraSpace/capra_space_720_frames" \
#       f_0449.png 450 -EnablePlugins=MovieRenderPipeline
#
# Why each step exists (see references/lessons.md):
# - out of process (-game): the in-editor PIE render crashed at Finalize;
# - refuse to start if another render runs: two renders share caches and
#   an orphaned job once wiped a live render;
# - bRemoteExecution=False: a remote "quit" meant for the editor killed a render;
# - poll for the last real frame, then kill -9: -game hangs or crashes after the
#   last frame (pad the sequence with one spare frame);
# - kill CrashReportClient: each orphan spins at 99% CPU.
# Projects with their own C++ module that won't load under -Cmd (Electric
# Dreams): set UE_BIN to the .app binary.
set -u
PROJ=$1 MAP=$2 QUEUE=$3 D=$4 LAST=$5 KEEP=${6:-0}
shift 5; (( $# )) && shift
UE_BIN=${UE_BIN:-"/Volumes/KB SS/Unreal Engine/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"}
RESX=${RESX:-1280}; RESY=${RESY:-720}
export DEVELOPER_DIR=${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}
LOGDIR="$(dirname "$D")/logs"; mkdir -p "$LOGDIR"; LOG="$LOGDIR/mrq-$(basename "$QUEUE")-$(date +%Y%m%d-%H%M%S).log"
if pgrep -f 'MoviePipelineConfig' >/dev/null; then echo "another render is running"; exit 1; fi
rm -rf "$D"
caffeinate -is "$UE_BIN" "$PROJ" "$MAP" -game -MoviePipelineConfig="$QUEUE" -windowed -resx=$RESX -resy=$RESY \
  -unattended -nosplash -NoLoadingScreen -log -stdout -FullStdOutLogOutput -notexturestreaming "$@" \
  "-ini:Engine:[/Script/PythonScriptPlugin.PythonScriptPluginSettings]:bRemoteExecution=False" > "$LOG" 2>&1 &
PID=$!
until [ -f "$D/$LAST" ]; do
  sleep 15
  kill -0 $PID 2>/dev/null || { [ -f "$D/$LAST" ] || { echo "render died at $(ls "$D" 2>/dev/null | wc -l | tr -d ' ') frames, log $LOG"; exit 1; }; }
done
sleep 20; kill -9 $PID 2>/dev/null; pkill -9 -f "MoviePipelineConfig=$QUEUE" 2>/dev/null; wait $PID 2>/dev/null
pkill -9 -x CrashReportClient 2>/dev/null
if (( KEEP > 0 )); then find "$D" -name 'f_*.png' | sort | tail -n +$((KEEP + 1)) | xargs rm -f; fi
echo "DONE $(basename "$QUEUE") frames=$(ls "$D" | grep -c png) dir=$D log=$LOG"
