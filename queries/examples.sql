-- top 10 conversations by message count
SELECT conversation, COUNT(*) AS msg_count FROM messages GROUP BY conversation ORDER BY msg_count DESC LIMIT 10;

-- messages in a conversation
SELECT time, author, message FROM messages WHERE conversation = 'copilot-activity-history' ORDER BY time LIMIT 200;

-- keyword search (basic)
SELECT rowid, conversation, time, author, message FROM messages WHERE message LIKE '%refund%' LIMIT 50;
