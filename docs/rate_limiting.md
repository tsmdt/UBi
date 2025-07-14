# Rate Limiting and Session Management

## Overview

AIMA now includes comprehensive rate limiting and session management features to prevent abuse and ensure fair usage of the system.

## Features

### 1. Character Limits

- **Per Request**: Maximum 2,000 characters per individual message
- **Per Session**: Maximum 20,000 characters total per session

### 2. Turn Limits

- **Per Session**: Maximum 20 conversation turns per session

### 3. Rate Limiting

- **Requests per Minute**: Maximum 10 requests per minute per session
- **Sliding Window**: Uses a 60-second sliding window for rate limiting

## Error Messages

When limits are exceeded, users receive clear German error messages:

- **Character limit per request**: "Sie haben die maximale Anzahl an Characters pro Anfrage erreicht (2000 Zeichen)."
- **Character limit per session**: "Sie haben die maximale Anzahl an Characters in dieser Session erreicht (20000 Zeichen)."
- **Turn limit per session**: "Sie haben die maximale Anzahl an Anfragen für diese Session erreicht (20 Anfragen)."
- **Rate limit**: "Zu viele Anfragen. Bitte warten Sie eine Minute, bevor Sie weitere Anfragen senden."

## Session Statistics

Users can check their current usage by typing any of these commands:
- `stats`
- `statistik`
- `statistiken`
- `nutzung`
- `usage`

This displays:
- Character usage with progress bar
- Turn usage with progress bar
- Rate limiting status
- Session duration
- Remaining limits

## Configuration

All limits can be configured in `code/config.py`:

```python
RATE_LIMIT_CONFIG = {
    "max_chars_per_request": 2000,    # Maximum characters per request
    "max_chars_per_session": 20000,   # Maximum characters per session
    "max_turns_per_session": 20,      # Maximum turns per session
    "max_requests_per_minute": 10,    # Maximum requests per minute
    "rate_limit_window": 60,          # Rate limit window in seconds
}
```

## Implementation Details

### Session Memory Integration

The rate limiting functionality is integrated into the existing `SessionMemory` class in `code/conversation_memory.py`:
- Extends `SessionContext` with rate limiting fields (`total_chars`, `total_turns`, `request_timestamps`)
- Adds rate limiting methods to `SessionMemory` class
- Uses the same session management infrastructure
- Automatic cleanup when sessions end

### Session Management

- Sessions are automatically created when users start chatting
- Session data is cleaned up when users end their chat
- Old sessions are automatically cleaned up after 1 hour of inactivity

### Integration

The rate limiting is integrated into the main message handler in `code/app.py`:
- Uses the existing `session_memory` instance for all rate limiting
- Checks are performed before processing any message
- Failed requests return immediately with error messages
- Successful requests are recorded for tracking
- No separate rate limiter instance needed

## Testing

Run the test suite to verify rate limiting functionality:

```bash
cd tests
python -m pytest test_rate_limiting.py -v
```

## Monitoring

The system provides session statistics that can be used for monitoring:
- Active session count
- Usage patterns
- Rate limit violations
- Session duration statistics

## Security Benefits

1. **Bot Protection**: Rate limiting prevents automated bots from overwhelming the system
2. **Resource Management**: Character and turn limits prevent excessive resource usage
3. **Fair Usage**: Ensures all users have equal access to the system
4. **Cost Control**: Limits help control API costs and system resources

## Future Enhancements

Potential improvements could include:
- IP-based rate limiting
- User authentication for higher limits
- Dynamic limits based on system load
- Analytics dashboard for usage monitoring
- Configurable limits per user type 