import { Button, Stack, TextField } from '@mui/material';
import React from 'react'
import { WebSocketConnectionContext, WebSocketConnectionState } from '../utils/WebSocketConnection';
import { ReadyState } from 'react-use-websocket';

export default function PolarConfig(props: any) {
    const {sendMessage, lastMessage, readyState} = React.useContext<WebSocketConnectionState>(WebSocketConnectionContext);
    const [address, setAddress] = React.useState("DF:EF:DB:F6:20:16");
    const [needsApply, setNeedsApply] = React.useState(false);

    React.useEffect(() => {
        if (readyState == ReadyState.OPEN) {
            handleApply();
        }
    }, [readyState]);

    React.useEffect(() => {
        console.log(lastMessage);
    }, [lastMessage]);

    const handleApply = () => {
        sendMessage(JSON.stringify({"command": "set_settings", "config": {"mac": address}}))
    }

    return (
        <Stack>
            <TextField disabled={props.started} id="polar-h10-address" label="Device MAC" variant="outlined" value={address} onChange={(event) => {setNeedsApply(true);setAddress(event.target.value)}}/>
            <Button onClick={handleApply} disabled={!needsApply || props.started} variant="contained">Apply</Button>
        </Stack>
    );
}