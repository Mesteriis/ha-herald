# Herald AI Notification Center

Herald is a Home Assistant notification control plane that sits between automations and users.
Automations publish semantic events. Herald decides who should get them, through which channel,
when they should be delivered, whether AI should rewrite them, and which room device should speak them.

## Core highlights

- thin semantic request contract through `herald.notify`
- per-user and per-room context enrichment from live Home Assistant state
- AI characters from `/config/herald/<character>/`
- queueing, deduplication, delay, and summaries
- room audio device fallback `Alice -> HomePod -> TV`
- Herald-owned runtime controls and diagnostics
- storage-mode dashboard registration and GitHub Pages documentation

## Maintainer

Aleksandr Meshchryakov <avm@sh-inc.ru>
