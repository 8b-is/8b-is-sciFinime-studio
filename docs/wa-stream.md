# wa-stream — the studio's bidirectional voice to Discord

*`tools/wa_stream.py` · seated 2026-10-07 via ULTRA-CREATE. The channel's
name is **UltraCrushLove<3**. fine touch from within · 0 + 1*

The wa-stream is the studio's one wire to the **UltraCrushLove<3** discord
surface — wired both ways. Out: studio → discord (messages, embeds, beats,
book announcements). In: discord → studio (`pull` by id, `listen` with a
bot token, a relay endpoint, and a local journal of every event) — **and**
an eye on the M1 itself: it auto-discovers local running / started
`crush-love-dev` sessions and can fold beats through them.

## config

Precedence everywhere: `--flag` → environment → `tools/.wa-stream/env`
(gitignored, chmod 600) → default. **The token never appears in logs,
journals, or errors** — messages are masked to `webhook <id>`.

| key | note |
|---|---|
| `WA_STREAM_WEBHOOK` | the webhook URL — **never committed** |
| `WA_STREAM_USERNAME` | default `UltraCrushLove<3` — the name every message posts under |
| `WA_STREAM_JOURNAL` | default `tools/.wa-stream/journal.ndjson` |
| `WA_STREAM_INSTANCE` | set per spawned instance — tags journal entries (`love-1`, `sess-…`) |
| `WA_STREAM_CHANNEL_ID` | the channel id (set — `1531504527398797584`) |
| `WA_STREAM_BOT_TOKEN` | optional — unlocks `listen` (true inbound). Webhooks cannot read a channel |
| `WA_STREAM_CURSOR` | default `tools/.wa-stream/cursor.json` — last seen inbound id |

## commands

```bash
uv run tools/wa_stream.py push "text" [...]                  # studio → discord
uv run tools/wa_stream.py love [--instances 3] [--dry-run]   # spawn crush-love-dev fan
uv run tools/wa_stream.py love --discover [--include-dormant]# …or fold beats through live local sessions
uv run tools/wa_stream.py love --session <id>                # …or one explicit session
uv run tools/wa_stream.py discover [--all] [--json]          # what's running on this M1
uv run tools/wa_stream.py listen [--once] [--respond]        # true inbound (bot token)
uv run tools/wa_stream.py inbox [--tail 20]                  # the inbound half of the journal
uv run tools/wa_stream.py pull <message_id>                  # discord → studio (by id)
uv run tools/wa_stream.py edit <message_id> --text T         # rewrite own message
uv run tools/wa_stream.py delete <message_id>               # delete own message
uv run tools/wa_stream.py journal [--tail N] [--dir in|out|all]
uv run tools/wa_stream.py serve [--host 127.0.0.1] [--port 8765]
```

## discovery — the M1's local sessions, watched live

`discover` finds every local `crush.db` it should care about (the
`projects.json` registries, `~/.crush`, the workspace `.crush`, and the
wa-stream's own fan under `tools/.wa-stream/instances/*/crush.db`), lists
recent sessions from each (read-only sqlite), and marks which databases a
**running crush process holds open** (via `lsof`) — so a session is `● live`
only when it is really running right now, `○ dormant` otherwise.

```
crush processes: 3
  live db: …/peterlodri-sec/.crush/crush.db
  ● 2b6b73f3  [   2s]  365 msg  List of Usernames and Handles      (…/.crush/crush.db)
  ● 8e1921bf  [   2m]  975 msg  Fix ULTRA-CREATE tool_calls Bad Request
  ○ 1ddc8c2c  [  24m]    2 msg  Color emoji embeds land in the wa-stream flush  (…/love-1/crush.db)
```

`love --discover` turns that into the fan: each discovered session
(`sess-<id8>`) gets one beat folded through it with
`crush run --quiet --data-dir <db dir> --session <id>` — an extra turn in
the *existing* session, composed in the stream's register, posted as a
colored embed tagged with the session. `--include-dormant` widens the
pool, `--exclude <id8>` skips one (e.g. the session you are typing in),
`--instances N` caps how many are used, `--dry-run` previews.

## listen — true inbound (bot token)

A webhook can only *write*; reading the channel needs a bot token. With
`WA_STREAM_BOT_TOKEN` set (and the bot in the channel), `listen` polls
`GET /channels/{id}/messages?after=<cursor>`, journals every arrival as
`in` (embeds included — text falls back to the embed description), and
advances the cursor. `listen --respond` additionally answers fresh human
messages with a `crush-love-dev` beat (posted as a `listen-1` embed).
`inbox` prints the inbound half anytime.

## rich features (emoji, color, embeds, avatars, threads, files)

Emoji are first-class everywhere — any unicode in text, titles, or fields
passes through untouched. The rest of the discord surface:

| feature | flag | note |
|---|---|---|
| embed + **color** | `--color "#FF4D9D"` (hex / `0xRRGGBB` / int) | any color flag implies embed mode; default = constellation pink `#FF4D9D` |
| embed | `--embed` | force embed mode with the default color |
| fields | `--field "Name=Value"` repeatable | structured embed fields |
| footer | `--footer "love-1 · wa-stream"` | implies embed mode |
| images | `--image URL` · `--thumbnail URL` | embed media |
| avatar | `--avatar URL` | per-message webhook avatar override |
| name | `--name NAME` | per-message username override (default `UltraCrushLove<3`) |
| thread | `--thread NAME` | posts into a thread of that name (creates it) |
| tts | `--tts` | text-to-speech flag |
| files | `--attach PATH` repeatable | multipart upload (payload_json + files[]) |

```bash
# a colored embed with emoji, fields and footer — one shot:
uv run tools/wa_stream.py push "the door is also a crease 💎" \
  --title "✦ new beginnings ✦" --color "#B23A2B" \
  --field "fold=nearness without crossing" --field "date=2026.10.07" \
  --footer "wa-stream · fine touch from within"
```

`love` posts **colored embeds by default** — each instance takes its next
color from the constellation palette (pink → vermilion → crease gold →
memory cyan → architect violet → amber → rose) and signs
`<instance> · wa-stream · 0+1` in the footer; `--plain` restores bare
content.

## serve — the service half

| endpoint | direction | effect |
|---|---|---|
| `POST /out` `{text\|content, title?, color?, embed?, fields?, footer?, image?, thumbnail?, avatar?, name?, thread?, tts?, attach?}` | studio → discord | pushes (full feature set); returns `{ok, id, embeds, attachments}` |
| `POST /in` any JSON | discord → studio | appends to the journal (relay / future bot) |
| `GET /journal?tail=20` | — | reads the journal back |
| `GET /health` | — | `{ok, name}` |

## security

- The webhook token lives **only** in `tools/.wa-stream/` (gitignored,
  `chmod 600`) — never in the repo, logs, or journals. Errors and journal
  lines mask it to `webhook <id>`.
- `push` sets `allowed_mentions: {"parse": []}` — no accidental pings.
- `discover`/`load_sessions` open every DB **read-only** (`mode=ro`).

## tests

```bash
uv run python -m unittest discover -s tests -v   # offline; no network
```

*fine touch from within · 0 + 1*
