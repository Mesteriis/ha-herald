# AI characters and rewriting

Herald loads character profiles from `/config/herald/<character>/`:

- `character.yaml`: name, description, and optional default selection.
- `system.jinja`: the character's voice and factual constraints.
- `notification.jinja`: individual ordinary notifications.
- `critical.jinja`: critical and security alerts.
- `short.jinja`: grouped notification summaries.
- `vocabulary.yaml`: preferred entity/name aliases.

The built-in Domovoy is a fairy-tale household guardian with rustic turns of
phrase and gentle humour. Ordinary notifications should have a recognizable
voice throughout their vocabulary and sentence structure; adding a catchphrase
to otherwise unchanged neutral prose is insufficient. Technical wording can
become clear household speech, such as a notification becoming a "весточка".
The message itself is paraphrased while preserving locations, numbers,
times, names, and urgency. Critical alerts start with the danger and location;
decorative phrases, jokes, and new instructions are excluded. Delivery room,
recipient, and delivery time are context for the listener, not facts about the
event.

Selecting a character alone does not enable rewriting. The request must allow
rewriting, and both the global AI switch and its severity switch must be enabled.
An explicit request character overrides the recipient/flow selection:

```yaml
action: herald.notify
data:
  event: washing_cycle_finished
  message: "Стиральная машина завершила стирку. Можно вынуть бельё."
  level: info
  rewrite: true
  summarize: false
  ai:
    character: domovoy
  channels:
    - persistent_default
```

This example records a notification in Home Assistant. AI output is variable;
inspect the actual rewritten message when checking the character's voice.
`_herald_ai_status: rewritten` means the title or message changed; it does not
prove that the spoken message changed. `unchanged` means the resulting title and
message matched the source.

Jinja files are read for each AI request, so editing a template applies to the
next rewrite without restarting HA. Profile metadata and vocabulary are loaded
when Herald initializes and require an integration reload after editing.

Default scaffolds create missing files only. Updating Herald preserves existing
character customizations. To adopt a new built-in Domovoy profile on an existing
installation, back up its directory and update the four Jinja templates
explicitly; a code update alone does not replace them.
