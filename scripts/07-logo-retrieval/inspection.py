def validate(records,assets):
 by={a['id'] for a in assets};errors=[]
 for a in assets:
  r=next((x for x in records if x.get('asset_id')==a['id']),None)
  if not r:errors.append('missing inspection: '+a['id'])
  elif r.get('inspection_status')!='accepted' or not r.get('evidence'):errors.append('incomplete inspection: '+a['id'])
 return errors
