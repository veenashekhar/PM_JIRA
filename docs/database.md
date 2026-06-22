# Database approach

This project will use SQLite with a minimal schema to support a single board per user for the MVP, while keeping the data model ready for multi-user use later.

## Tables

- users
  - id (primary key)
  - username (unique)
  - password_hash
  - created_at

- boards
  - id (primary key)
  - user_id (foreign key -> users.id)
  - title
  - created_at

- columns
  - id (primary key)
  - board_id (foreign key -> boards.id)
  - title
  - position (integer order within board)

- cards
  - id (primary key)
  - board_id (foreign key -> boards.id)
  - column_id (foreign key -> columns.id)
  - title
  - details
  - position (integer order within column)
  - created_at
  - updated_at

## Notes

- MVP authentication is a single hardcoded user, but the schema supports multiple users.
- A single board per user is enforced at the application layer for now.
- Columns are fixed in count but title is editable; order is stored as position.
- Cards move across columns and within a column by updating column_id and position.

## Data structure example

See docs/kanban-data-structure.json for an example representation of the data model.
