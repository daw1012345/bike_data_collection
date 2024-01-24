import { Typography } from '@mui/material';
import { Stack } from '@mui/system';
import React from 'react'
import { WebSocketConnectionContext, WebSocketConnectionState } from '../utils/WebSocketConnection';
import { ReadyState } from 'react-use-websocket';

export default function ConnectionStatus() {
    const {readyState} = React.useContext<WebSocketConnectionState>(WebSocketConnectionContext);

    const getStateName = (state: ReadyState) => {
        switch (state) {
            case ReadyState.UNINSTANTIATED:
                return "ERROR!"
            case ReadyState.CLOSED:
                return "Not Connected"
            case ReadyState.CLOSING:
                return "Disconnecting"
            case ReadyState.CONNECTING:
                return "Connecting..."
            case ReadyState.OPEN:
                return "Connected"
            default:
                return "ERROR!"
        }
    }

    return (
        <Stack direction="row" spacing={2}>
            <Typography variant="h4" style={{backgroundColor: readyState === ReadyState.OPEN ? "green" : "red"}}>
                Connection State: {getStateName(readyState)}
            </Typography>
        </Stack>
    );
    }