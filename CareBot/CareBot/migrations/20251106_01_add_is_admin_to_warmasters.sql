-- Add is_admin field to warmasters table
-- depends:

-- Add is_admin column with default value of 0 (not admin)
ALTER TABLE warmasters ADD COLUMN is_admin INTEGER DEFAULT 0;
