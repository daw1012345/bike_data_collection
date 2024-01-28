import { Chip, Stack, Typography } from '@mui/material';
import React from 'react'
import { WebSocketConnectionContext } from '../utils/WebSocketConnection';

export default function ButtonStatus() {
    const [recent, setRecent] = React.useState("--");
    const {lastMessage} = React.useContext(WebSocketConnectionContext);
    React.useEffect(() => {
        if (lastMessage == null) {
            return;
        }

        const msg = JSON.parse(lastMessage.data)
        if (msg["component"] != "buttons" || msg["data"] == null) {
            return;
        }

        if (msg["data"]["button"] != null) {
            setRecent(msg["data"]["button"]);
        }

    }, [lastMessage])
    return (
        <Stack direction="row" spacing={2}>
            <Typography variant="h6">Recently Pressed Button:</Typography>
            <Chip label={recent}></Chip>
        </Stack> 
    );
}