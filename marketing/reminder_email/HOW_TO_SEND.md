# Sending the Lost Souls reminder email from Eventbrite

What is in this folder:

| File | What it is |
|---|---|
| `reminder_email.html` | The finished email as HTML (600px, works on phones, dark theme) |
| `qr_check.png` | The diamond QR code, purple with the keyhole, that opens the phone check |
| `door66-logo.png` | The logo used in the header |
| `HOW_TO_SEND.md` | This file |

The QR code and the button both open **https://lostsouls.door66.events/check/**.
I decoded the QR image with a real QR reader and it returns exactly that address.

## Before you send anything

1. **The site must be live with the check page and the two email images.** The email
   shows its logo and QR from the website, because Eventbrite cannot attach files.
   Open both in a browser and confirm they show:
   - https://lostsouls.door66.events/assets/images/email/door66-logo.png
   - https://lostsouls.door66.events/assets/images/email/qr-check.png
   - https://lostsouls.door66.events/check/ (on your own phone, tap through it once)
2. If the site is not deployed yet, the email's images will be broken. Merge and
   deploy first.

## What Eventbrite documents

(From Eventbrite's help article "Email your registered attendees":
https://www.eventbrite.com/help/en-us/articles/484221/how-to-email-your-attendees-through-eventbrite/ ;
I could not open it directly, so this comes from its search summary. Check the wording in your account.)

- Open your event, then **Manage attendees**, then **Emails to attendees**, then a new email.
  If you do not see it, the account owner needs to give you permission in organization settings.
- Fill in Name, Reply-to email, To, Subject and Message.
- You **cannot attach files**. You can link to things hosted elsewhere. That is why the
  QR image lives on the website.
- You can **send a test email to yourself** before sending.
- You can **send now or schedule**. Emails can go out while the event is live and up to
  10 days after it ends.
- "All attendees" only reaches people who are registered **at the moment you send**.
  Anyone who buys later does not get it, so send a second one to late buyers.
- Do not paste from Word or Google Docs. It can bring hidden formatting. Paste as plain text.
- The email sits in an Eventbrite template. You can toggle the event cover image, name,
  date, time and location, and there is a button that goes to the attendee's order or the
  event page.

## What I could not confirm

I could not find a source that says whether Eventbrite's message box accepts **raw HTML**,
lets you **insert an image into the body**, or lets you point its button at **your own link**.
So do this two-minute check first, in a draft:

1. Look at the message toolbar. Is there an **image** icon? A **link** icon? A
   **source code / `<>`** button?
2. Send yourself a test and look at it on your phone and on a computer.

Then pick the matching path.

## Path A: the editor has a source / HTML view

1. Open `reminder_email.html` in a text editor and copy everything between `<body …>` and
   `</body>` (the whole outer `<table>`), not the `<head>`.
2. Paste it into the source view, switch back, and send a test.
3. If Eventbrite strips the layout (it may remove tables or colours), use Path B.

## Path B: plain rich-text editor (the likely case)

Build it by hand with the text below.

1. **Subject** (suggestion): `One small ritual before Lost Souls`
2. **Message**, pasted as plain text, then formatted:

```
You’re confirmed for Lost Souls at Bembridge House.

One small ritual before you cross the threshold.

The spirits of Bembridge House make themselves known through your phone’s camera. Before your evening with us, let’s make sure yours is ready to see them.

Follow the single step it gives you. It will ask to use your camera — choose Allow. That’s the whole ritual.

On your phone? Tap below:
Prepare my phone →

At your computer? Scan this with your phone’s camera:
```

3. Make **Prepare my phone →** a link to `https://lostsouls.door66.events/check/`
   (bold, and on its own line so it is easy to tap).
4. **The QR code:**
   - If the editor has an **image** option, insert `qr_check.png` from this folder, or use
     the address https://lostsouls.door66.events/assets/images/email/qr-check.png
   - If it does not, write the line **Show the QR code** and link it to
     `https://lostsouls.door66.events/assets/images/email/qr-check.png`.
     On a computer that opens the QR alone on screen, ready to scan with a phone.
5. **Eventbrite's own button.** If the template has a "view order" or "event page" button,
   switch it off if you can. It points somewhere else and would compete with ours.
6. Optional: turn on the event cover image or name in the template if you like the look.

## Send checklist

- [ ] The two image addresses above load, and the check page works on a real phone
- [ ] Reply-to is an address you read (guests will reply to this)
- [ ] Sent a test to yourself and opened it **on a phone** and **on a computer**
- [ ] Tapped "Prepare my phone" in the test and ran the whole check
- [ ] Scanned the QR from the computer screen with a phone and it opened the check
- [ ] Recipients: all attendees
- [ ] Scheduled for about a week before the event, so anyone with a camera problem has
      time to fix it. Send the same email again to anyone who registered later.

## If a guest says it did not work

The page tells them what to do. The usual fixes are: open the link in Safari (iPhone) or
Chrome (Android) and not inside the email app, choose **Allow** when the camera asks, and
do not use a private or incognito window. The page lists these steps and shows
inquiries@door66.events.
