 ignore_devices = [
     # Add ids of devices to be ignored here
 ]
 
 ignore_entities = [
     # Add entities whose devices should be ignored here
 ]
 
 CHECKER_ID = "pyscript.device_availability_checker"
 
 from homeassistant.helpers import entity_registry as erm
 from homeassistant.helpers import device_registry as drm
 
 from homeassistant.const import STATE_UNAVAILABLE
 
 @service 
 @time_trigger('cron(*/30 * * * *)')
 def device_availability_checker_cron():
     er = erm.async_get(hass)
     dr = drm.async_get(hass)
     
     unavailable_devices = {}
     unavailable_since = {}
     
     # Iterate over all devices and check whether they are unavailable
     # A device is supposed to be unavailable if all related entities are in
     # state "unavailable"
     for d in dr.devices:
         if d in ignore_devices:
             continue
         unavailable = False
         since = None
         for e in erm.async_entries_for_device(er, d):
             if e.entity_id in ignore_entities:
                 unavailable = False
                 break
             elif hass.states.is_state(e.entity_id, STATE_UNAVAILABLE):
                 unavailable  = True
                 since = hass.states.get(e.entity_id).last_changed
             else:
                 unavailable = False
                 break
         if unavailable:
             unavailable_devices[d] = dr.async_get(d)
             unavailable_since[d] = since
     
     notifs = []
     devices = {}
     
     # Iterate over all unavailable devices and construct notification text
     # for a persistent_notification
     for k, d in unavailable_devices.items():
         manufacturer = d.manufacturer
         model = d.model
         text = f'- {d.name}'
         desc = ""
         if model is not None:
             desc += model
         if manufacturer is not None:
             if desc != "":
                 desc += f" [{manufacturer}]"
             else:
                 desc += manufacturer
         if desc != "":
             text += "\n    - " + desc
         text += f"\n    - Since: {unavailable_since[k]}"
         text += f"\n    - ID: {d.id}"
         
         devices[k] = {
             "name": d.name,
             "manufacturer": manufacturer,
             "model": model,
             "since": unavailable_since[k]
         }
         
         notifs.append(text)
     
     # Show a persistent notification or dismiss an old one if there is nothing
     # to show
     ntext = "\n".join(notifs)
     if ntext != "":
         hass.services.async_call("persistent_notification", "create", {
             "notification_id": "device_availability_warning",
             "title": "List of Unavailable Devices",
             "message": ntext
         }, False)
     else:
         hass.services.async_call("persistent_notification", "dismiss", {
             "notification_id": "device_availability_warning"
         }, False)
     
     state.set(CHECKER_ID, len(devices), devices = devices)
 
 
 @time_trigger('startup')
 def device_availability_checker_startup_trigger():
     log.info("device_availability_checker.startup_trigger()")
     task.sleep(60)
     device_availability_checker_cron()
