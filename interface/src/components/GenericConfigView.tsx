import { Divider, Paper, Stack, Switch, Typography } from '@mui/material';
import React, { lazy, useState } from 'react'

export interface GenericConfigViewProps {
    name: string;
    slug: string;

    statusElem: any | undefined;
    configElem: any | undefined;

    isEnabled: (name: string) => boolean;
    setStatus: (name: string, stat: boolean) => void;
    started: boolean;
}

export default function GenericConfigView(props: GenericConfigViewProps) {
    const {name, slug, statusElem, configElem} = props;

    return (
        <Stack>
          <Paper sx={{px: 6, pb: 4}} variant="outlined">
            <Stack direction="row" alignItems="center" spacing={2}>
                <Typography sx={{py: 4}} variant="h3">{name}</Typography>
                <Switch inputProps={{ 'aria-label': 'controlled' }} disabled={props.started} checked={props.isEnabled(slug)} onChange={(evt) => {props.setStatus(slug, evt.target.checked)}}/>
            </Stack>
           
            {props.statusElem != null && props.isEnabled(props.slug) && 
                statusElem
            }
            {props.configElem != null && props.isEnabled(props.slug) && 
            <>
                {configElem}
                <Divider sx={{m: 2}}/>
            </>
            }
          </Paper>
        </Stack>
    );
}