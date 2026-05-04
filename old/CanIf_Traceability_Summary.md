# CanIf Traceability Matrix — OpenSAR (ArcCore)
## Source: communication/CanIf/CanIf.c (996 lines, 30 functions)
## Standard: AUTOSAR SWS_CanIf R4.0

---

## Status Legend
| Symbol | Meaning |
|--------|---------|
| IMPL | Fully implemented |
| IMPL* | Conditionally implemented (#if guard) |
| NOSUP | Not supported (returns E_NOT_OK / CANIF_E_NOK_NOSUPPORT) |
| EXT | ArcCore extension (not in AUTOSAR standard) |

---

## 1. Initialization Requirements

| Req_ID | SWS_Ref | Description | Function | Lines | Status |
|--------|---------|-------------|----------|-------|--------|
| CANIF001 | SWS_CANIF_00001 | Init all internal variables, set module initialized | CanIf_Init | 131–146 | IMPL |
| CANIF007 | SWS_CANIF_00007 | Set all controller modes to CS_STOPPED on init | CanIf_Init | 139 | IMPL |
| CANIF008 | SWS_CANIF_00008 | Set all PDU modes to GET_OFFLINE on init | CanIf_Init | 140 | IMPL |
| CANIF066 | SWS_CANIF_00066 | Access CAN Driver configuration data (CanControllerConfigType) | CanIf_InitController | 185–199 | IMPL |
| CANIF092 | SWS_CANIF_00092 | Stop controller if STARTED before re-init; DET if invalid mode | CanIf_InitController | 168–175 | IMPL |
| CANIF293 | SWS_CANIF_00293 | Call Can_InitController during CanIf_InitController | CanIf_InitController | 200 | IMPL |

---

## 2. Controller Mode Management

| Req_ID | SWS_Ref | Description | Function | Lines | Status |
|--------|---------|-------------|----------|-------|--------|
| CANIF017 | SWS_CANIF_00017 | Transition to CS_STARTED; set PDU mode ONLINE; call CAN_T_START | CanIf_SetControllerMode | 248–268 | IMPL |
| CANIF021 | SWS_CANIF_00021 | Transition to CS_SLEEP via STOPPED; call CAN_T_SLEEP (Figure 33) | CanIf_SetControllerMode | 271–289 | IMPL |
| CANIF022 | SWS_CANIF_00022 | Transition to CS_STOPPED; set PDU mode OFFLINE; call CAN_T_STOP | CanIf_SetControllerMode | 291–311 | IMPL |
| CANIF023 | SWS_CANIF_00023 | GetControllerMode returns current mode via output pointer | CanIf_GetControllerMode | 322–335 | IMPL |

---

## 3. PDU Mode Management

| Req_ID | SWS_Ref | Description | Function | Lines | Status |
|--------|---------|-------------|----------|-------|--------|
| CANIF072 | SWS_CANIF_00072 | SetPduMode transitions between all 7 PDU channel modes | CanIf_SetPduMode | 544–630 | IMPL |
| CANIF075 | SWS_CANIF_00075 | GetPduMode returns current channel PDU mode | CanIf_GetPduMode | 632–646 | IMPL |

---

## 4. Transmission

| Req_ID | SWS_Ref | Description | Function | Lines | Status |
|--------|---------|-------------|----------|-------|--------|
| CANIF005 | SWS_CANIF_00005 | CanIf_Transmit requests L-PDU transmission via CAN Driver | CanIf_Transmit | 423–482 | IMPL |
| CANIF011 | SWS_CANIF_00011 | Call Can_Write with HTH and PDU data | CanIf_Transmit | 469 | IMPL |
| CANIF161 | SWS_CANIF_00161 | Check CS_STARTED before tx; handle CAN_BUSY (no buffering) | CanIf_Transmit | 450–479 | IMPL |
| CANIF082 | SWS_CANIF_00082 | Handle CAN_BUSY return (tx buffer not supported) | CanIf_Transmit | 475–479 | IMPL |
| CANIF189 | SWS_CANIF_00189 | SetDynamicTxId updates CAN ID of a dynamic L-PDU at runtime | CanIf_SetDynamicTxId | 647–683 | IMPL |
| CANIF209 | SWS_CANIF_00209 | CancelTxConfirmation (transmit cancellation) | CanIf_CancelTxConfirmation | 901–914 | NOSUP |

---

## 5. Reception

| Req_ID | SWS_Ref | Description | Function | Lines | Status |
|--------|---------|-------------|----------|-------|--------|
| CANIF020 | SWS_CANIF_00020 | RxIndication distributes received frame to upper layer | CanIf_RxIndication | 763–898 | IMPL |
| CANIF025 | SWS_CANIF_00025 | Discard frame if PDU channel mode disables receiver path | CanIf_RxIndication | 776–788 | IMPL |
| CANIF060 | SWS_CANIF_00060 | Software filtering on BASIC CAN HRH using mask/ID | CanIf_RxIndication | 796–820 | IMPL* |
| CANIF026 | SWS_CANIF_00026 | DLC check on received L-PDU (conditional compile) | CanIf_RxIndication | 823–829 | IMPL* |
| CANIF208 | SWS_CANIF_00208 | Call PduR_CanIfRxIndication for PDUs via PDU Router | CanIf_RxIndication | 853–864 | IMPL* |
| CANIF233 | SWS_CANIF_00233 | Call CanNm_RxIndication for CAN NM PDUs | CanIf_RxIndication | 846–851 | IMPL* |

---

## 6. Notifications / Callbacks

| Req_ID | SWS_Ref | Description | Function | Lines | Status |
|--------|---------|-------------|----------|-------|--------|
| CANIF013 | SWS_CANIF_00013 | TxConfirmation notifies upper layer of successful transmission | CanIf_TxConfirmation | 742–761 | IMPL |
| CANIF053 | SWS_CANIF_00053 | Upper layer TX callback only called when PDU mode allows TX | CanIf_TxConfirmation | 754–758 | IMPL |
| CANIF019 | SWS_CANIF_00019 | ControllerBusOff sets controller STOPPED and notifies upper layer | CanIf_ControllerBusOff | 917–942 | IMPL |
| CANIF037 | SWS_CANIF_00037 | SetWakeupEvent propagates wakeup to EcuM | CanIf_SetWakeupEvent | 943–962 | IMPL |

---

## 7. Status/Notification Read APIs (Not Supported)

| Req_ID | SWS_Ref | Description | Function | Lines | Status |
|--------|---------|-------------|----------|-------|--------|
| CANIF194 | SWS_CANIF_00194 | ReadRxPduData copies received Rx data to buffer | CanIf_ReadRxPduData | 487–497 | NOSUP |
| CANIF202 | SWS_CANIF_00202 | ReadTxNotifStatus returns TX notification status | CanIf_ReadTxNotifStatus | 503–527 | NOSUP |
| CANIF207 | SWS_CANIF_00207 | ReadRxNotifStatus returns RX notification status | CanIf_ReadRxNotifStatus | 533–539 | NOSUP |

---

## 8. Transceiver APIs (Not Supported)

| Req_ID | SWS_Ref | Description | Function | Lines | Status |
|--------|---------|-------------|----------|-------|--------|
| CANIF034 | SWS_CANIF_00034 | SetTransceiverMode | CanIf_SetTransceiverMode | 684–692 | NOSUP |
| CANIF038 | SWS_CANIF_00038 | GetTransceiverMode | CanIf_GetTransceiverMode | 693–701 | NOSUP |
| CANIF039 | SWS_CANIF_00039 | GetTrcvWakeupReason | CanIf_GetTrcvWakeupReason | 702–710 | NOSUP |
| CANIF040 | SWS_CANIF_00040 | SetTransceiverWakeupMode | CanIf_SetTransceiverWakeupMode | 711–720 | NOSUP |
| CANIF041 | SWS_CANIF_00041 | CheckWakeup | CanIf_CheckWakeup | 722–729 | NOSUP |
| CANIF042 | SWS_CANIF_00042 | CheckValidation | CanIf_CheckValidation | 730–739 | NOSUP |

---

## 9. ArcCore Extensions (Not in AUTOSAR Standard)

| Req_ID | Description | Function | Lines | Status |
|--------|-------------|----------|-------|--------|
| ARC_PreInit | Pre-init CAN controller before CanIf_Init completes | CanIf_PreInit_InitController | 206–222 | EXT |
| ARC_FindHrh | Map HRH hardware object to CanIf channel ID | CanIf_Arc_FindHrhChannel | 100–126 | EXT |
| ARC_FindTxPdu | Find Tx PDU config entry by PDU ID (bounds check) | CanIf_FindTxPduEntry | 343–354 | EXT |
| ARC_FindRxPdu | Find Rx PDU config entry by PDU ID (runtime config) | CanIf_FindRxPduEntry | 357–364 | EXT |
| ARC_GetRxHandler | Get receive HRH handler for channel (runtime config) | CanIf_Arc_GetReceiveHandler | 366–391 | EXT |
| ARC_GetTxHandler | Get transmit HTH handler for channel (runtime config) | CanIf_Arc_GetTransmitHandler | 393–421 | EXT |
| ARC_Error | Notify upper layer of CAN driver error | CanIf_Arc_Error | 963–990 | EXT |
| ARC_GetChanDefConf | Return default config index for channel | CanIf_Arc_GetChannelDefaultConfIndex | 991–996 | EXT |

---

## 10. DET Error Coverage Map

| DET Error ID | AUTOSAR Meaning | Functions That Validate It |
|-------------|-----------------|---------------------------|
| CANIF_E_UNINIT | Module not initialized | Init, SetControllerMode, GetControllerMode, Transmit, SetPduMode, GetPduMode, SetDynamicTxId, TxConfirmation, RxIndication, CancelTxConfirmation, ControllerBusOff, SetWakeupEvent, Arc_Error |
| CANIF_E_PARAM_CONTROLLER | Invalid controller index | InitController, PreInit, SetControllerMode, GetControllerMode, SetPduMode, GetPduMode, ControllerBusOff, SetWakeupEvent, Arc_Error |
| CANIF_E_PARAM_POINTER | NULL pointer argument | Init, InitController, GetControllerMode, Transmit, RxIndication, CancelTxConfirmation |
| CANIF_E_PARAM_CONTROLLER_MODE | Controller not in valid mode for operation | InitController (CANIF092) |
| CANIF_E_PARAM_HRH | Invalid Hardware Receive Handle | Arc_FindHrhChannel, Arc_GetReceiveHandler, RxIndication |
| CANIF_E_PARAM_LPDU | Invalid L-PDU (PDU ID out of range) | TxConfirmation, RxIndication, CancelTxConfirmation |
| CANIF_E_INVALID_TXPDUID | Invalid TX PDU ID | Transmit, ReadTxNotifStatus, SetDynamicTxId |
| CANIF_E_PARAM_CANID | Invalid CAN ID | SetDynamicTxId |
| CANIF_E_PARAM_DLC | Received DLC smaller than configured | RxIndication (CANIF_DLC_CHECK==STD_ON) |
| CANIF_E_NOK_NOSUPPORT | Feature not supported by this implementation | ReadRxPduData, ReadTxNotifStatus, ReadRxNotifStatus, SetTransceiverMode, GetTransceiverMode, GetTrcvWakeupReason, SetTransceiverWakeupMode, CheckWakeup, CheckValidation, CancelTxConfirmation |

---

## Coverage Summary

| Category | Total Reqs | Implemented | Not Supported | ArcCore Extension |
|----------|-----------|-------------|--------------|-------------------|
| Initialization | 6 | 6 | 0 | 0 |
| Controller Mode | 4 | 4 | 0 | 0 |
| PDU Mode | 2 | 2 | 0 | 0 |
| Transmission | 6 | 5 | 1 | 0 |
| Reception | 6 | 6 | 0 | 0 |
| Notifications | 4 | 4 | 0 | 0 |
| Status Read APIs | 3 | 0 | 3 | 0 |
| Transceiver APIs | 6 | 0 | 6 | 0 |
| ArcCore Extensions | 8 | 0 | 0 | 8 |
| **TOTAL** | **45** | **27** | **10** | **8** |

**Implementation Rate (standard AUTOSAR reqs): 27/37 = 73%**
**Not-supported features are flagged via CANIF_E_NOK_NOSUPPORT DET errors**
