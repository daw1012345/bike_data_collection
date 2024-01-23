import { Chip, Stack, Typography } from '@mui/material';
import React, { useState } from 'react'
import { WebSocketConnectionContext } from '../utils/WebSocketConnection';

export default function ButtonStatus() {
    const [recent, setRecent] = React.useState("--");
    const {lastMessage} = React.useContext(WebSocketConnectionContext);
    React.useEffect(() => {
        if (lastMessage == null) {
            return;
        }

        const msg = JSON.parse(lastMessage.data)
        if (msg["component"] != "button" || msg["data"] == null) {
            return;
        }

        if (msg["data"]["recent"] != null) {
            setRecent(msg["data"]["recent"]);
        }

    }, [lastMessage])
    return (
        <Stack direction="row" spacing={2}>
            <Typography variant="h6">Recently Pressed Button:</Typography>
            <Chip label={recent}></Chip>
        </Stack> 
    );
}