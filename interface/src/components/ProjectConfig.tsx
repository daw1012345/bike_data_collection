import { Button, Stack, TextField } from '@mui/material';
import React from 'react'
import { WebSocketConnectionContext } from '../utils/WebSocketConnection';

export default function ProjectConfig(props: any) {
    const {sendMessage, lastMessage} = React.useContext(WebSocketConnectionContext)
    const [name, setName] = React.useState(`project-${new Date().toJSON()}`);
    const [transitioning, setTransition] = React.useState(false);

    React.useEffect(() => {
        if (lastMessage == null) {
            return;
        }

        const msg = JSON.parse(lastMessage.data)

        if ((msg["command"] === "start" || msg["command"] === "stop")) {
            setTransition(false);
            if (msg["result"] === true) {
                props.setStarted(!props.started);
            }
        }

    }, [lastMessage]);

    const handleStart = () => {
        // props.setStarted(true);
        setTransition(true);
        sendMessage(JSON.stringify({"command": "start", "project": name}))
    }

    const handleStop = () => {
        // props.setStarted(false);
        setTransition(true);
        sendMessage(JSON.stringify({"command": "stop"}))
    }

    return (
        <Stack>
            <TextField disabled={props.started || transitioning} value={name} onChange={(event) => {setName(event.target.value)}} id="project-name" label="Project Name" variant="outlined"/>
            <Stack direction="row">
                <Button onClick={handleStart} disabled={props.started || transitioning} variant="contained">Start</Button>
                <Button onClick={handleStop} disabled={!props.started || transitioning} variant="contained">Stop</Button>
            </Stack>
        </Stack>
    );
}