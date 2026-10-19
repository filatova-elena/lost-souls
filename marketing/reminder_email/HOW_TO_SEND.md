# Send the reminder from Eventbrite

**Before you start:** the site must be live (the email's logo and QR load from it). Check
https://lostsouls.door66.events/assets/images/email/qr-check.png shows an image, and
https://lostsouls.door66.events/check/ works on your phone.

## Steps

1. Eventbrite → your event → **Manage attendees** → **Emails to attendees** → new email.
2. **Reply-to:** an address you read. **To:** all attendees.
3. **Subject:** `One small ritual before Lost Souls`
4. **Message:** paste this as plain text:

```
You’re confirmed for Lost Souls at Bembridge House.

One small ritual before you cross the threshold.

The spirits of Bembridge House make themselves known through your phone’s camera. Before your evening with us, let’s make sure yours is ready to see them.

Follow the single step it gives you. It will ask to use your camera — choose Allow. That’s the whole ritual.

On your phone? Tap below:
Prepare my phone →

At your computer? Scan this with your phone’s camera:
```

5. Make **Prepare my phone →** a bold link to `https://lostsouls.door66.events/check/`.
6. **QR code:** insert `qr_check.png` from this folder. No image button? Write
   "Show the QR code" and link it to
   `https://lostsouls.door66.events/assets/images/email/qr-check.png`.
7. Switch off Eventbrite's own "view order" button if it lets you.
8. **Send a test to yourself.** Open it on your phone, tap the button, and run the check.
9. **Schedule** it for about a week before the event.

Shortcut: if the editor has a source / HTML view, paste everything inside `<body>` of
`reminder_email.html` instead of steps 4–6, then test.

Late buyers don't get it ("all attendees" means everyone registered when you send), so
send it again to them later.
