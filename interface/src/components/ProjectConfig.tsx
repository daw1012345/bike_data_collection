import { Button, Stack, TextField } from '@mui/material';
import React, { useEffect, useState } from 'react'
import { WebSocketConnectionContext } from '../utils/WebSocketConnection';

export default function ProjectConfig(props) {
    const {sendMessage} = React.useContext(WebSocketConnectionContext)
    const [name, setName] = React.useState(`project-${new Date().toJSON()}`);

    const handleStart = () => {
        props.setStarted(true);
        sendMessage(JSON.stringify({"command": "start", "project": name}))
    }

    const handleStop = () => {
        props.setStarted(false);
        sendMessage(JSON.stringify({"command": "stop"}))
    }

    return (
        <Stack>
            <TextField value={name} onChange={(event) => {setName(event.target.value)}} id="project-name" label="Project Name" variant="outlined"/>
            <Stack direction="row">
                <Button onClick={handleStart} disabled={props.started} variant="contained">Start</Button>
                <Button onClick={handleStop} disabled={!props.started} variant="contained">Stop</Button>
            </Stack>
        </Stack>
    );
}