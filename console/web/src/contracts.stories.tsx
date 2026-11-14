import {useState} from 'react';
import type {Meta,StoryObj} from '@storybook/react-vite';
import {expect,userEvent,within} from 'storybook/test';
import {ContractCard} from './contracts.tsx';
import {ToastProvider} from './ui.tsx';
import type {Contract} from '../../contracts.ts';
const contract:Contract={id:'contract',version:3,organizationId:'acme',title:'Signed agreement',reference:'ACME-2026',status:'active',externalReferences:[{system:'CRM',reference:'deal-42'}],documents:[{id:'pdf',filename:'agreement.pdf',size:1024,sha256:'abcdef1234567890',uploadedAt:'2026-11-14T12:00:00Z'}],evidence:[{kind:'override',entityId:'terms:seats',documentId:'pdf',page:2,note:'Signed allowance'}],history:[{at:'2026-11-14T12:00:00Z',actor:'alice@example.test',action:'link_evidence',reason:'Signed'}]};
function Example(){const [sent,setSent]=useState('');return <ToastProvider><ContractCard contract={contract} basePath="/unused" overrides={[{id:'terms:seats',privilege:'Seats'}]} grants={[]} busy={false} change={async label=>{setSent(label);}}/><p role="status">{sent}</p></ToastProvider>;}
const meta={title:'Workspace/Contract evidence',component:Example} satisfies Meta<typeof Example>;
export default meta;
type Story=StoryObj<typeof meta>;
export const PrivateEvidence:Story={play:async({canvasElement})=>{const c=within(canvasElement);await expect(c.getByRole('heading',{name:'Signed agreement'})).toBeInTheDocument();await expect(c.getByText('Signed allowance')).toBeInTheDocument();await expect(c.getByRole('button',{name:'Attach PDF'})).toBeDisabled();await userEvent.selectOptions(c.getByLabelText('Supporting PDF'),'pdf');await userEvent.type(c.getByLabelText('Page (optional)'),'3');await userEvent.selectOptions(c.getByLabelText('Override or grant'),'override:terms:seats');await userEvent.click(c.getByRole('button',{name:'Link evidence'}));await expect(c.getByText('Link entitlement evidence',{exact:true})).toBeInTheDocument();canvasElement.dataset.playComplete='true';}};
