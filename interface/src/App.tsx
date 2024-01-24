import React from 'react'
import CssBaseline from '@mui/material/CssBaseline';
import ConnectionStatus from './components/ConnectionStatus'
import { WebSocketConnectionContext} from './utils/WebSocketConnection';
import { Paper, Skeleton, Stack, Typography } from '@mui/material';
import PolarConfig from './components/PolarConfig';
import PolarStatus from './components/PolarStatus';
import ProjectConfig from './components/ProjectConfig';
import ButtonStatus from './components/ButtonStatus';
import GenericConfigView from './components/GenericConfigView';
import { ReadyState } from 'react-use-websocket';

function App() {
  const [started, setStarted] = React.useState(false);
  const [enabled, setEnabled] = React.useState<string[]>([]);
  const [synced, setSynced] = React.useState(false);
  const {sendMessage, lastMessage, readyState} = React.useContext(WebSocketConnectionContext);
  // TODO: Make URL the hostname of rpi for auto-connection

  React.useEffect(() => {
    if (lastMessage == null) {
      return;
    }

    const msg = JSON.parse(lastMessage.data);

    if (msg["result"] != null && msg["result"] !== true) {
      alert(`ERROR: ${msg["message"] == null ? "unknown" : msg["message"]}`);
    }

    if (msg["command"] !== "get_state") {
      return;
    }

    if (msg["message"]["collectors"] == null || msg["message"]["is_running"] == null) {
      return;
    }

    console.log(msg)
    setStarted(msg["message"]["is_running"]);
    setEnabled(msg["message"]["collectors"]);
    setSynced(true);

  }, [lastMessage]);

  React.useEffect(() => {
    console.log(readyState);
    if (readyState === ReadyState.OPEN) {
      console.log("Sent")
      sendMessage(JSON.stringify({command: "get_state"}));
    }
  }, [readyState]);

  React.useEffect(() => {
    if (synced) {
      sendMessage(JSON.stringify({command: "set_collectors", collectors: enabled}));
    }
  }, [enabled]);

  const setState = (name: string, state: boolean) =>  {
    if (state && !enabled.includes(name)) {
      setEnabled([name, ...enabled]);
    }

    if (!state && enabled.includes(name)) {
      const newEnabled = enabled.filter(item => item != name);
      setEnabled(newEnabled);
    }
  }

  const enabledStateProps = {isEnabled: (name: string) => {return enabled.includes(name)}, setStatus: setState, started: started};

  if (synced) {
    return (
      <React.Fragment>
        <CssBaseline/> 
        
        <Stack spacing={2}>
          <ConnectionStatus/>
       
        {/* <GenericConfigView name="session" slug="session" statusElem={<PolarStatus/>} configElem={<PolarConfig started={started}/>} {...enabledStateProps}/> */}
        <Stack direction={{xs: "column", md: "row"}} spacing={2}>
          <Paper sx={{px: 6, pb: 4}} variant="outlined">
            <Stack spacing={2}>
            <Typography sx={{py: 4}}variant="h3">Session</Typography>
              <ProjectConfig started={started} setStarted={setStarted}/>
            </Stack>
          </Paper>
  
  
          <GenericConfigView name="Polar H10" slug="polar" statusElem={<PolarStatus/>} configElem={<PolarConfig started={started}/>} {...enabledStateProps}/>
          {/* <Stack>
            <Paper sx={{px: 6, pb: 4}} variant="outlined">
              <Typography sx={{py: 4}} variant="h3">Polar H10</Typography>
              <PolarStatus/>
              <Divider sx={{m: 2}}/>
              <PolarConfig started={started}/>
            </Paper>
          </Stack> */}
          <GenericConfigView name="Buttons" slug="buttons" statusElem={<ButtonStatus/>} configElem={null} {...enabledStateProps}/>
          {/* <Stack>
            <Paper sx={{px: 6, pb: 4}} variant="outlined">
              <Typography sx={{py: 4}}variant="h3">Buttons</Typography>
              <ButtonStatus/> */}
              {/* <Divider sx={{m: 2}}/>
              <PolarConfig started={started}/> */}
            {/* </Paper>
          </Stack> */}
  
        </Stack>
        </Stack>
      </React.Fragment>
    // <p>AA</p>
    )
  } else {
    return (<Skeleton/>);
  }


}

export default App
