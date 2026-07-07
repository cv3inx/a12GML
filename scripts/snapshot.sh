#!/bin/bash
# Save/restore container snapshots
# Usage: ./snapshot.sh save <name>    - save current state
#        ./snapshot.sh restore <name> - restore from snapshot
#        ./snapshot.sh list           - list snapshots

ACTION="${1:-list}"
NAME="${2}"
CONTAINER="redroid-gml"

case "$ACTION" in
    save)
        [ -z "$NAME" ] && { echo "Usage: $0 save <name>"; exit 1; }
        echo "[*] Saving snapshot: $NAME"
        docker commit "$CONTAINER" "redroid-gml-snap:${NAME}"
        echo "[✓] Saved as redroid-gml-snap:${NAME}"
        ;;
    restore)
        [ -z "$NAME" ] && { echo "Usage: $0 restore <name>"; exit 1; }
        if ! docker image inspect "redroid-gml-snap:${NAME}" &>/dev/null; then
            echo "[!] Snapshot not found: $NAME"
            echo "    Available: $(docker images --format '{{.Tag}}' redroid-gml-snap 2>/dev/null | tr '\n' ' ')"
            exit 1
        fi
        echo "[*] Restoring snapshot: $NAME"
        docker stop "$CONTAINER" 2>/dev/null
        docker rm "$CONTAINER" 2>/dev/null
        # Re-run with the snapshot image
        PORT=$(docker inspect "$CONTAINER" 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin)[0]['HostConfig']['PortBindings']['5555/tcp'][0]['HostPort'])" 2>/dev/null || echo "5555")
        sed "s|IMAGE=.*|IMAGE=\"redroid-gml-snap:${NAME}\"|" /opt/a12GML/run.sh | bash
        echo "[✓] Restored from $NAME"
        ;;
    list)
        echo "Available snapshots:"
        docker images --format "  {{.Tag}}\t{{.CreatedSince}}\t{{.Size}}" redroid-gml-snap 2>/dev/null || echo "  (none)"
        ;;
    delete)
        [ -z "$NAME" ] && { echo "Usage: $0 delete <name>"; exit 1; }
        docker rmi "redroid-gml-snap:${NAME}" 2>/dev/null
        echo "[✓] Deleted: $NAME"
        ;;
    *)
        echo "Usage: $0 {save|restore|list|delete} [name]"
        ;;
esac
