SELECT id, user_id, question, response, latency_ms, created_at
FROM chat_logs
WHERE user_id = :user_id
ORDER BY id DESC
LIMIT 20;
