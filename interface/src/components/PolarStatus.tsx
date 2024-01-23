import React, { useEffect, useState } from 'react'
import { WebSocketConnectionContext } from '../utils/WebSocketConnection';
import { Chip, Stack, Typography } from '@mui/material';

export default function PolarStatus() {
    const [accelStatus, setAccelStatus] = React.useState("--");
    const [hrStatus, setHrStatus] = React.useState("--");
    const {lastMessage} = React.useContext(WebSocketConnectionContext);

    useEffect(() => {
        if (lastMessage == null) {
            return;
        }

        const msg = JSON.parse(lastMessage.data)
        if (msg["component"] != "polar" || msg["data"] == null) {
            return;
        }

        if (msg["data"]["acc"] != null) {
            setAccelStatus(msg["data"]["acc"]);
        }

        if (msg["data"]["ecg"] != null) {
            setHrStatus(msg["data"]["ecg"]);
        }

    }, [lastMessage]);

    return (
    <Stack>
        <Stack direction="row" spacing={2}>
            <Typography variant="h6">HeartRate Data Sample:</Typography>
            <Chip label={hrStatus}/>
        </Stack>
        <Stack direction="row" spacing={2}>
            <Typography variant="h6">Accelerometer Data Sample:</Typography>
            <Chip label={accelStatus}/>
        </Stack>
    </Stack>);
}