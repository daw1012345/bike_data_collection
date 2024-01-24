import React from 'react'
import useWebSocket, { ReadyState } from 'react-use-websocket';

export interface WebSocketConnectionProviderProps {
    url: string;
    children: React.ReactNode;
}

export interface WebSocketConnectionState {
    readonly sendMessage: any;
    readonly lastMessage: any;
    readonly readyState: ReadyState;
}

export function WebSocketConnectionProvider(props: WebSocketConnectionProviderProps) {
    const { sendMessage, lastMessage, readyState } = useWebSocket(props.url);

    return (
        <WebSocketConnectionContext.Provider value={{sendMessage: sendMessage, lastMessage, readyState}}>
            {props.children}
        </WebSocketConnectionContext.Provider>
    )
}

export const WebSocketConnectionContext = React.createContext<WebSocketConnectionState>({
    sendMessage: () => {},
    lastMessage: "",
    readyState: ReadyState.UNINSTANTIATED
})