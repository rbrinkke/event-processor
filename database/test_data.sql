-- Test Data voor event_outbox table
-- Insert verschillende event types voor testing

-- User Events
INSERT INTO event_outbox (
    event_id,
    aggregate_id,
    aggregate_type,
    event_type,
    payload,
    status,
    created_at
) VALUES
(
    gen_random_uuid(),
    gen_random_uuid(),
    'User',
    'UserCreated',
    '{"email": "test@example.com", "username": "testuser", "first_name": "Test", "last_name": "User"}'::jsonb,
    'pending',
    NOW()
),
(
    gen_random_uuid(),
    gen_random_uuid(),
    'User',
    'UserUpdated',
    '{"email": "updated@example.com", "first_name": "Updated"}'::jsonb,
    'pending',
    NOW()
);

-- Activity Events
INSERT INTO event_outbox (
    event_id,
    aggregate_id,
    aggregate_type,
    event_type,
    payload,
    status,
    created_at
) VALUES
(
    gen_random_uuid(),
    gen_random_uuid(),
    'Activity',
    'ActivityCreated',
    '{"title": "Test Activity", "description": "Test description", "creator_user_id": "123e4567-e89b-12d3-a456-426614174000", "max_participants": 10}'::jsonb,
    'pending',
    NOW()
),
(
    gen_random_uuid(),
    gen_random_uuid(),
    'Activity',
    'ParticipantJoined',
    '{"user_id": "123e4567-e89b-12d3-a456-426614174001"}'::jsonb,
    'pending',
    NOW()
);

-- Display inserted data
SELECT
    event_id,
    aggregate_type,
    event_type,
    status,
    created_at
FROM event_outbox
ORDER BY sequence_id;
