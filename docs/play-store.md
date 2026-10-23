# Google Play checklist (free app)

What the app now has for Google Play's rules, and what to fill in on the Play Console.

## On the server

Set these where the server starts (the PC's start script):

- `ADMIN_USERNAMES=admin` lets that player review reports (🚩 Reports on the website; a push
  notification arrives when there's a new one). Comma-separate several names.
- `CONTACT_EMAIL=you@example.com` shows a contact address on the privacy policy page.
- Password reset emails: `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM`.
  Free with Gmail: `SMTP_HOST=smtp.gmail.com`, your Gmail address as `SMTP_USER`, and an
  [app password](https://myaccount.google.com/apppasswords) as `SMTP_PASSWORD`. Without these,
  the reset link is only written to the server's log.
- Backups: run `python scripts/backup.py --db <demo.db> --uploads <uploads folder> --to D:/CaptureAnimals/backups`
  daily with Task Scheduler (keeps 14 database copies and a mirror of the photos).

## Play Console answers

- **Privacy policy URL:** https://kurosatto.github.io/CollectAnimals/privacy.html
- **Community rules (UGC policy):** https://kurosatto.github.io/CollectAnimals/rules.html, agreed to at sign-up
- **Account deletion URL:** https://kurosatto.github.io/CollectAnimals/delete-account.html
  (in the app: Account → Delete account)
- **Target audience:** 13 and older. Choosing under-13 brings in the Families policy.
- **Content rating:** players share photos and comments, with reporting and blocking.
- **Ads:** none. **In-app purchases:** none.
- **Data safety** (all sent over HTTPS, deletable on request, nothing shared with third parties):
  - Personal info: email address, username (account management)
  - Photos (app functionality)
  - Approximate and precise location, optional (app functionality)
  - App activity: in-app actions (likes, friends) and other user-generated content (comments), for app functionality
  - Not collected: contacts, payment info, device or advertising IDs, health, files

Those two pages are `docs/privacy.html` and `docs/delete-account.html`, published free by GitHub Pages
(repo Settings → Pages → Deploy from branch `main`, folder `/docs`). They stay up when the PC is off,
and the delete page finds the game server's current address the same way the app does. The server
also serves the policy at `/privacy` and the delete page at `/delete-account`.

## Play builds

- The "new version is available" APK prompt is skipped when Google Play installed the app
  (Play's rules forbid updating outside Play); demo APK installs still get it.

## Still needed outside the code

- A Google Play developer account ($25 once).
- A closed test with at least 12 testers for 14 days before going public.
- Store listing text, screenshots and the 512 px icon.
