import {useState} from 'react';
import type {Meta,StoryObj} from '@storybook/react-vite';
import {expect,userEvent,within} from 'storybook/test';
import {Organizations} from './organizations.tsx';
import {emptyData,type Organization} from '../model/model.ts';
import type {Workspace,Save} from './app.tsx';

function Example({withTier=false}:{withTier?:boolean}){
 const [workspace,setWorkspace]=useState<Workspace>(()=>{
  const data=emptyData();
  if(withTier){data.tiers=[{id:'basic',name:'Basic',rank:0,gracePeriodDays:0}];data.variants=[{id:'basic_standard',tierId:'basic',name:'Basic standard',kind:'standard',values:{}}];}
  return {id:'example',name:'Example',role:'Owner',revision:1,data};
 });
 const save:Save=async(_section,entry)=>{
  const org=entry as Organization;
  setWorkspace(w=>({...w,data:{...w.data,organizations:[org]}}));
  return true;
 };
 return <Organizations workspace={workspace} save={save} canEdit busy={false}/>;
}
const meta={title:'Workspace/Organizations',component:Example} satisfies Meta<typeof Example>;
export default meta;
type Story=StoryObj<typeof meta>;
async function create(canvasElement:HTMLElement){
 const c=within(canvasElement);
 await userEvent.click(c.getByRole('button',{name:'Add organization'}));
 await userEvent.type(c.getByLabelText('Name'),'Acme');
 await userEvent.click(c.getByRole('button',{name:'Save organization'}));
 await expect(c.getByText('Unassigned',{exact:true})).toBeInTheDocument();
 await userEvent.click(c.getByRole('button',{name:'Edit organization'}));
 return c;
}
export const WithoutTiers:Story={play:async({canvasElement})=>{
 const c=await create(canvasElement);
 await expect(c.queryByLabelText('Tier variant')).not.toBeInTheDocument();
 canvasElement.dataset.playComplete='true';
}};
export const OptionalAssignment:Story={args:{withTier:true},play:async({canvasElement})=>{
 const c=await create(canvasElement);
 await expect(c.getByLabelText('Tier variant')).toHaveValue('');
 await userEvent.selectOptions(c.getByLabelText('Tier variant'),'basic_standard');
 await userEvent.click(c.getByRole('button',{name:'Save organization'}));
 await expect(c.getByText('Basic standard · Active')).toBeInTheDocument();
 await userEvent.click(c.getByRole('button',{name:'Edit organization'}));
 canvasElement.dataset.playComplete='true';
}};
