# Plan

- [x] 1. Update design
- [x] 2. After a question search, clicking a video takes the user to the matching minute
- [x] 3. Add a contact button to "The transcription is AI-generated and may contain errors. We welcome your feedback." — linked to an email (TBD, to be provided)
- [x] 4. Add a "Contact us" button that opens the email (TBD, to be provided)
  - 3 & 4 stay hidden until `CONTACT_EMAIL` is set for the web app (`web/.env.local` locally, `.env.production` on the server — no rebuild needed)
- [ ] 5. Add pagination (scroll to load more)
- [ ] 6. Add subject filter *(later)*
- [ ] 7. Create a script to copy data from the hard drive, excluding `.mp3`, old `.npy`, `.wav`, and audio segments
