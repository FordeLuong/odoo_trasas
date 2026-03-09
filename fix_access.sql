UPDATE documents_document SET access_internal='edit', confidential_level='public' WHERE type!='folder' AND (access_internal='none' OR access_internal IS NULL);
