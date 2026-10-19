#!/bin/zsh
# Preflight for /kb-unreal: what's available on this machine right now.
#   ~/.claude/skills/kb-unreal/scripts/preflight.sh
# Read-only. Prints the drive, engine, tools, projects and samples present,
# free disk, and any Unreal editors or renders already running.
KB="/Volumes/KB SS"
UE="$KB/Unreal Engine/UE_5.8/Engine/Binaries/Mac"
ok() { print -- "  [ok]   $1"; }
no() { print -- "  [--]   $1"; }
chk() { [[ -e "$2" ]] && ok "$1  ($2)" || no "$1  (missing: $2)"; }

print "Drive and engine"
[[ -d "$KB" ]] && ok "KB SS mounted, free: $(df -h "$KB" | awk 'NR==2{print $4}')" || no "KB SS NOT mounted — most projects live there"
chk "Unreal 5.8 editor" "$UE/UnrealEditor.app/Contents/MacOS/UnrealEditor"
chk "Unreal 5.8 Cmd" "$UE/UnrealEditor-Cmd"
[[ -f "$KB/Unreal Engine/UE_5.8/Engine/Build/Build.version" ]] && ok "engine $(python3 -c "import json;d=json.load(open('$KB/Unreal Engine/UE_5.8/Engine/Build/Build.version'));print('%s.%s.%s CL %s'%(d['MajorVersion'],d['MinorVersion'],d['PatchVersion'],d['Changelist']))")"
print "Internal disk free: $(df -h / | awk 'NR==2{print $4}')"

print "\nTools"
chk "Blender" "/Applications/Blender.app/Contents/MacOS/Blender"
command -v ffmpeg >/dev/null && ok "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')" || no "ffmpeg not on PATH"
chk "TrailGoat venv (numpy, Pillow)" "$HOME/Desktop/Projects/TrailGoat/.venv/bin/python"
chk "kb-ytvideo venv" "$HOME/Library/Application Support/kb-ytvideo/venv/bin/python"
chk "Xcode (Metal toolchain)" "/Applications/Xcode.app/Contents/Developer"
chk "Capra run_remote.py" "$HOME/Desktop/Projects/Caprastudios/unreal/run_remote.py"
chk "Capra sound library" "$HOME/Desktop/Projects/Caprastudios/output/unreal/sfx/library/LICENSE.md"

print "\nProjects (Kris's work)"
for p in "Unreal Projects/Intro_motion/Intro_motion.uproject" "Unreal Projects/CapraSpace/CassiniSample.uproject" \
         "Unreal Projects/TrailGoatElectricDream/ElectricDreamsSample.uproject" "TrailGoat-Studio/ParticleLab/ParticleLab.uproject" \
         "TrailGoat-Studio/WSER/WSER.uproject" "HostileTakeover/unreal/HostileTakeover.uproject" "Unreal Engine/Amandine_OW/Amandine_OW.uproject"; do
  chk "$(basename "$(dirname "$p")")" "$KB/$p"
done
chk "Capra_intro (studies)" "$HOME/Documents/Unreal Projects/Capra_intro/Capra_intro.uproject"

print "\nEpic samples"
for p in "CassiniSample/CassiniSample.uproject" "ContentExamples/ContentExamples.uproject" \
         "ICVFXProductionTest/ICVFXProductionTest.uproject" "ProjectTitan/ProjectTitan.uproject"; do
  chk "$(dirname "$p")" "$KB/Unreal Projects/$p"
done
chk "GameAnimationSample" "/Volumes/KB SS/Unreal Projects/GameAnimationSample/GameAnimationSample.uproject"
chk "NiagaraExamples" "/Volumes/KB SS/Unreal Projects/NiagraExamples/NiagraExamples.uproject"
ls "$KB/Unreal Projects" 2>/dev/null | while read -r n; do
  case "$n" in Intro_motion|CapraSpace|TrailGoatElectricDream|CassiniSample|ContentExamples|ICVFXProductionTest|ProjectTitan|GameAnimationSample|NiagraExamples|VaultCache) ;; *) print "  [new?] $KB/Unreal Projects/$n — not in the capability map yet";; esac
done

print "\nRunning now"
pgrep -fl 'UnrealEditor' | grep -v -E 'grep|CrashReport|EditorServices' | sed -E 's/^([0-9]+) .*\/([^\/]+\.uproject).*/  pid \1  \2/' | sort -u
pgrep -f 'MoviePipelineConfig' >/dev/null && print "  [!!]   a Movie Render Queue render is running — don't start another or send remote Python to it"
pgrep -x CrashReportClient >/dev/null && print "  [!!]   CrashReportClient running (kill it: pkill -9 -x CrashReportClient)"
true
