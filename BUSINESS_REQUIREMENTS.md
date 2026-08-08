# Business Requirements: Family Diary

## 1. Purpose

Family Diary is a public diary-style application for publishing family growth records and daily life stories. The first version will present content written in Markdown and deployed to Vercel, making the published diary easy for anyone to read while ensuring personal information and credentials are carefully removed before publication.

## 2. Business Goals

- Provide a simple, trusted place for publishing family memories and growth records.
- Reduce the friction of recording day-to-day moments, milestones, and important events.
- Help visitors browse and reflect on past entries by date, person, topic, or media.
- Ensure all published content is anonymized and safe for public access.
- Ensure no credentials, secrets, tokens, or private configuration values appear in any published content.
- Present entries with a modern diary-like reading experience.
- Support long-term retention of family history in a format that remains usable over time.

## 3. Target Users

- Parents or guardians who want to publish selected family growth records and memories.
- Family members who help prepare or review diary entries before publication.
- Public visitors who read the published diary content.
- Future family members who may browse historical entries as an archive.

## 4. Scope

### In Scope

- Publish diary entries from Markdown content in the first version.
- Deploy the application to Vercel first.
- Allow anyone to view published diary contents without authentication.
- Review and verify every published content item to ensure personal information is anonymized.
- Scan content to ensure credentials, secrets, tokens, and private configuration values are not displayed.
- Attach photos or other media to entries only when they have been reviewed for public safety.
- Associate entries with anonymized family member labels.
- Record important milestones, events, and dates.
- Browse entries chronologically.
- Search or filter entries by anonymized family member label, date, keyword, or category.
- Provide data backup or export capabilities.
- Provide a modern UI that visually feels like reading a diary.

### Out of Scope for Initial Release

- Public social networking features beyond public read-only access to published diary content.
- Open user registration for unrelated users.
- Advertising or third-party content feeds.
- Complex AI-generated memory summaries unless explicitly added later.
- Medical, legal, or official child record management.
- In-browser content authoring workflows, unless added after the Markdown-first version.

## 5. Functional Requirements

### Diary Entries

- Diary entries are authored and stored as Markdown files in the first version.
- Each entry can include title, body, date, optional author label, and optional tags.
- Each entry can be marked as a milestone or ordinary diary note.
- The application renders Markdown content into public diary pages.
- The application must not render unpublished draft content to public visitors.
- Media attachments can be referenced from Markdown only after the media has been reviewed for public safety.

### Publication and Deployment

- The first deployment target is Vercel.
- The application should be compatible with Vercel's deployment workflow.
- Published pages should be statically renderable where practical to improve performance and reliability.
- Build or release workflows should include checks that prevent accidental publication of unsafe content.

### Family Members

- Public-facing family member labels must be anonymized or pseudonymous.
- Entries can be associated with anonymized family member labels.
- Users can filter entries by anonymized family member label.
- Real names, exact birth dates, addresses, school names, workplace names, and other identifying details must not be published unless explicitly reviewed and approved.

### Timeline and Browsing

- The system displays entries sorted by entry date in descending order by default, with the latest entries first.
- Users can browse entries by month, year, or specific date.
- Users can view milestone entries separately from ordinary diary entries.
- Timeline, archive, milestone, and search listings are paginated with a user-selectable page size of 5, 10, or 20 entries per page, defaulting to 5 entries per page.

### Search and Organization

- Users can search entries by keyword.
- Users can filter entries by date range, family member, tag, or milestone status.
- Users can add tags to support custom organization.

### Content Safety and Anonymization

- Published content is public and viewable by anyone.
- Every content item must be scanned and manually verified before publication to ensure personal information is anonymous.
- The application must not display credentials, API keys, access tokens, passwords, private URLs, environment variables, or other secrets in any content.
- Content review must check text, Markdown metadata, links, image filenames, image contents, alt text, and embedded media.
- The release process should fail or block publication when likely personal information or credentials are detected.

### UI and Reading Experience

- The UI should visually feel like reading a diary while remaining modern and polished.
- Diary entries should prioritize readability, calm spacing, clear typography, and chronological context.
- Diary entry cards on timeline, archive, milestone, and search pages should use a layered box-shadow to create a subtle 3D card look.
- The design should support both mobile and desktop reading.
- The interface should avoid visual clutter that distracts from diary content.

### Export and Backup

- Users can export diary content in a portable format.
- The system should support backup and recovery of entries and media.

## 6. Non-Functional Requirements

- The application should be easy to use on mobile and desktop devices.
- Common actions such as adding a Markdown entry or reviewed media file should be quick and simple.
- The system should preserve diary content reliably over long periods.
- Page load and navigation performance should remain responsive as the number of entries grows.
- Uploaded media should be stored securely and delivered efficiently.
- The application should be designed with public-read safety, anonymization, and credential prevention as core concerns.
- The application should deploy cleanly to Vercel in the first version.
- Markdown rendering should be safe and should not allow unsafe scripts or uncontrolled HTML injection.
- The visual design should combine diary-like warmth with modern usability and responsive layout.

## 7. Data Requirements

Core data entities should include:

- Publisher or maintainer
- Family or diary collection
- Anonymized family member label
- Diary entry
- Media attachment
- Tag
- Publication review status
- Comment or reaction, if collaboration is included later

Diary entries should retain creation time, update time, entry date, optional author label, associated anonymized family member labels, Markdown content, tags, milestone status, and publication review metadata.

Markdown files and frontmatter must not contain credentials, secrets, exact personal identifiers, or private operational data.

## 8. Success Metrics

- Users can create a new diary entry in under one minute.
- Users can find a past entry by date, anonymized family member label, or keyword without manual scrolling.
- Public visitors can read published diary entries without signing in.
- Published diary content does not expose personal information that identifies family members.
- Published diary content does not expose credentials, API keys, tokens, passwords, or private configuration values.
- The site deploys successfully to Vercel.
- The UI is recognizably diary-like while meeting modern readability expectations.
- Exported data can be restored or reused outside the application.
- The product supports steady long-term use without requiring frequent maintenance from the user.

## 9. Risks and Considerations

- Family data is sensitive, so public publication requires strict anonymization and review.
- Credentials or private configuration values accidentally committed to Markdown, frontmatter, images, links, or generated pages would create significant risk.
- Images may contain identifying details such as faces, locations, school uniforms, documents, street signs, or metadata.
- Large photo collections may increase storage and backup costs.
- Long-term value depends on data portability and durability.
- The product should avoid becoming too complex for quick daily use.
- Public visibility may require a clearer editorial policy for what is safe to publish.

## 10. Open Questions

- Should the application support multiple diary collections?
- What anonymization standard should be used before content is approved for publication?
- Should automated personal-information and credential scanning be required in CI before every Vercel deployment?
- What media types should be supported in the first release?
- Is offline access required?
- Should entries support public comments or reactions, or remain read-only?
- What export formats are required?
- Should images be stripped of metadata before publication?
