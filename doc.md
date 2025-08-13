# Label & Message & DB Conclusion
There are 26229 failed records in April, extract accumulate top 90% failure descriptions (symptom_labels) 

- [Label \& Message \& DB Conclusion](#label--message--db-conclusion)
    - [Labels that are not able to match](#labels-that-are-not-able-to-match)
    - [Symptom Labels without matching issues](#symptom-labels-without-matching-issues)
    - [Symptom Labels with unique standard message but not all of the messages are match](#symptom-labels-with-unique-standard-message-but-not-all-of-the-messages-are-match)
    - [Symptom Labels that have some standard messages are matched](#symptom-labels-that-have-some-standard-messages-are-matched)
    - [Labels without standard message patterns](#labels-without-standard-message-patterns)
    - [Check database content](#check-database-content)
    - [Conclusion](#conclusion)

### Labels that are not able to match
> 10 labels with 16.75%

| Failure Description                                        | Percentage |
|------------------------------------------------------------|------------|
| SDC First Fail of test-completion-missing-error for retest | 7.23%      |
| HB16 PCIe link speed and width check                       | 5.02%      |
| Foxconn BMC validation                                     | 1.19%      |
| Diorite PCIe link speed and width check                    | 0.87%      |
|  *(Blank)*                                                 | 0.56%      |
| hwinterface_smoke_test-hwinterface-error                   | 0.55%      |
| io adapter location validation failure                     | 0.42%      |
| Software Exception                                         | 0.30%      |
| pcierrors-high-surprise_down_error-rate                    | 0.30%      |
| Kernel pretty_name is not matched.                         | 0.30%      |

1. **SDC First Fail of test-completion-missing-error for retest**

   i.e.  FWI2430-05795

   ```plaintext
   {
      'symptom_msg': "Create Diorite SSH Connection failed.\nCan not connect to Diorite IP: 'fd00::D63A:2CFF:FEFC:64E4'",
      'symptom_label': 'Diorite SSH Connection Failed'
   },
   {
      'symptom_msg': 'Command \'rsync -s -e "sshpass -p 0vss ssh -o ServerAliveInterval=600" "root@[192.168.200.131]:/tmp/cpu_checker_burnin_stderr_5cdc1f56-d041-4f5e-a787-0143c1702bf7.log" "/tmp/              cpu_checker_burnin_stderr_5cdc1f56-d041-4f5e-a787-0143c1702bf7_2kg5vz6r.log"\' returned non-zero exit status 255.',
      'symptom_label': 'rsync-error'
   },
   {
      'symptom_msg': 'Unable to connect to 192.168.200.131: [Errno 113] No route to host',
      'symptom_label': 'Create Host SSH Connection failed'
   },
   {
      'symptom_msg': "String 'PciBus: Discovered PCI @ [01|00|00]' not found during booting.",
      'symptom_label': 'Diorite PCI string checking'
   },
   {
      'symptom_msg': 'Diag execution failed.',
      'symptom_label': 'test-completion-missing-error-cpu_checker_burnin'
   }
   ```

2. **HB16 PCIe link speed and width check**

   | Label                                                            | Message Format                                             | Notes                                           |
   |------------------------------------------------------------------|------------------------------------------------------------|-------------------------------------------------|
   | PCIe device existence on PE?.IO0                                 | value=&#39;False&#39; lower_limit=&#39;True&#39; upper_limit=&#39;&#39;            | ? = 2 / 3 / 4 / 5                               |
   | PCIe device link speed at /phys/PE?/IO0:device:xxxx              | value=&#39;??GT/s&#39; lower_limit=&#39;16.0GT/s&#39; upper_limit=&#39;&#39;      | ? = 2 / 3 / 4 / 5<br>?? = 2.5 / 5.0              |
   | PCIe device link width at /phys/PE?/IO0:device:xxxx              | value=&#39;x??&#39; lower_limit=&#39;x16&#39; upper_limit=&#39;&#39;                | ? = 2 / 3 / 4 / 5<br>?? = 1 / 2 / 4 / 8       |


3. **Foxconn BMC validation**

   | Label                                   | Message Format                                                                                                 | Notes                                                                                  |
   |-----------------------------------------|-----------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
   | BMC bmc version                         | value='fbmc, dev, ???' lower_limit='fbmc, local, 24.49.0.0' upper_limit=''                                      | ??? = random string                                                               |
   | BMC bmc version                                      | value='gbmc, dev, ???' lower_limit='fbmc, local, 24.49.0.0' upper_limit=''                                      | ??? = random string                                                                                     |
   | BMC bmc version                                        | value='gbmc, local, ???' lower_limit='fbmc, local, 24.49.0.0' upper_limit=''                                    | ??? = random string                                                                                      |
   | attribute-error-exception              | Caught AttributeError exception.\nTraceback (most recent call last): ???                                        | ??? = traceback content (flexible)                                                    |
   | no-output-detected                      | Either failed to trigger the diag or the diag sent a blank response.                                            | Fixed message                                                                          |
   | rocedural-error                         | ???: failed to connect to all addresses;<br>last error: UNKNOWN: unix:/var/run/gsysd/grpc.socket: !!! [UNAVAILABLE] | ??? =  Failed to + GetFirmwareInfo / GetMemoryInfo / GetNetworkInterfaceInfo / GetPsuInfo / enumerate EEPROMs / get GetVersion / get plugins from GetNodeInfo <br> ??? = Hwinterface + GetCpuInfo / GetNodeInfo / GetStorageInfo + failed <br> !!! = No such file or directory / Connection refused |
   | task-failed-with-non-zero-code-return-code | Task return code: 1.                                                                                           | Fixed message                                                                          |
   | test-completion-missing-error-dna       | /bin/sh: 1: /export/hda3/meltan/dna/dna: not found                                                              | Fixed message                                                                          |


4. **Diorite PCIe link speed and width check**

   | Label                                                            | Message Format                                             | Notes                                           |
   |------------------------------------------------------------------|------------------------------------------------------------|-------------------------------------------------|
   | PCIe device existence on PE?.IO0                                 | value=&#39;False&#39; lower_limit=&#39;True&#39; upper_limit=&#39;&#39;            | ? = 0 ~ 5                               |
   | PCIe device link speed at /phys/PE?/IO0:device:xxxx              | value=&#39;??GT/s&#39; lower_limit=&#39;16.0GT/s&#39; upper_limit=&#39;&#39;      | ? = 2 / 3 / 4 / 5<br>?? = 2.5 / 5.0              |
   | PCIe device link width at /phys/PE?/IO0:device:xxxx              | value=&#39;x??&#39; lower_limit=&#39;x16&#39; upper_limit=&#39;&#39;                | ? = 2 / 3 / 4 / 5<br>?? = 1 / 2 / 4 / 8       |

5. **hwinterface_smoke_test-hwinterface-error**

   | Label                                                            | Message Format                                             | Notes                                           |
   |------------------------------------------------------------------|------------------------------------------------------------|-------------------------------------------------|
   | hwinterface_smoke_test-hwinterface-error                         | HWInterface ? failed: failed to connect to all addresses; last error: UNKNOWN: unix:/var/run/gsysd/grpc.socket: No such file or directory            | ? = GetCpuInfo / GetVersion                               |
   | procedural-error                                                 | Failed to ?: failed to connect to all addresses; last error: UNKNOWN: unix:/var/run/gsysd/grpc.socket: No such file or directory [UNAVAILABLE]'      | ? = GetFirmwareInfo / GetMemoryInfo / GetNetworkInterfaceInfo / GetPsuInfo / enumerate EEPROMs / GetVersion / plugins from GetNodeInfo              |
   | procedural-error                                                      | Hwinterface ? failed: failed to connect to all addresses; last error: UNKNOWN: unix:/var/run/gsysd/grpc.socket: No such file or directory [UNAVAILABLE]                | ? = GetCpuInfo / GetNodeInfo / GetStorageInfo       |
   | process-plan-aborted                                             | Process plan was aborted by user in this step.      | Fixed message                                          |
   | task-failed-with-non-zero-code-return-code                       | Task return code: 1.                                | Fixed message                                          |

6. **io adapter location validation failure**

   | Label                                                            | Message Format                                             | Notes                                           |
   |------------------------------------------------------------------|------------------------------------------------------------|-------------------------------------------------|
   | io adapter location validation failure                           | Component io adapter SN xxxx location: PE?, expected location: PE?'| xxxx: Random SN <br>  ? = 0 ~ 7         |

7. **Kernel pretty_name is not matched.**

   | Label                                                            | Message Format                                             | Notes                                           |
   |------------------------------------------------------------------|------------------------------------------------------------|-------------------------------------------------|
   | Kernel pretty_name is not matched.                               | kernel_pretty_name Expected: Poky (Yocto Project Reference Distro) 4.0.23 (kirkstone), Current: Poky (Yocto Project Reference Distro) 4.0.?? (kirkstone), device_id: , unit:            | ?? = 11 / 23                        


8. **Software Exception**
   * No correspond symptom_info

9. **pcierrors-high-surprise_down_error-rate**
   | Label                                                            | Message Format                                             | Notes                                           |
   |------------------------------------------------------------------|------------------------------------------------------------|-------------------------------------------------|
   | error-monitor-procedural-error                                   | Test failed: INTERNAL: One of the monitors failed          | Fixed message                                   |
   | load-hwinfo-fail                                                 | Failed to load hwinfos for PMBUS_ERROR_MONITOR monitor: NOT_FOUND: could not resolve to devpath          | Fixed message                                   |
   | pcierrors-low-mc_blocked_tlp-rate <br> pcierrors-low-bad_tlp-rate <br> pcierrors-low-poisoned_tlp-rate <br> pcierrors-low-receiver_error-rate <br> pcierrors-low-tlp_prefix_blocked_error-rate <br> pcierrors-low-lane_error-rate <br> pcierrors-low-completion_timeout-rate <br> pcierrors-low-corrected_internal_error-rate <br> pcierrors-low-bad_dllp-rate <br> pcierrors-low-data_link_protocol_error-rate <br> pcierrors-low-unexpected_completion-rate <br> pcierrors-low-flow_control_protocol_error-rate <br> pcierrors-low-replay_num_rollover-rate <br> pcierrors-low-surprise_down_error-rate <br> pcierrors-low-header_log_overflow-rate <br> pcierrors-low-malformed_tlp-rate <br> pcierrors-low-replay_timer_timeout-rate <br> pcierrors-low-receiver_overflow-rate <br> pcierrors-low-completer_abort-rate <br> pcierrors-low-uncorrectable_internal_error-rate <br> pcierrors-low-acs_violation-rate <br> pcierrors-low-atomic_ops_egress_blocked-rate <br> pcierrors-low-ecrc_error-rate <br>| PCIe serial number: xxx, location: 0000:??:01.1, devpath: /phys/!!:xxx pcie error are below thresholds.      | xxx: random serial number / pathname <br> ??: possible location <br> !!: CPU0/1 / PE0 ~ 8|
   | pcierrors-high-replay_num_rollover-rate <br> pcierrors-high-bad_dllp-rate <br> pcierrors-high-lane_error-rate <br> pcierrors-high-receiver_error-rate <br> pcierrors-high-header_log_overflow-rate <br> pcierrors-high-surprise_down_error-rate <br> pcierrors-high-data_link_protocol_error-rate <br> pcierrors-high-bad_tlp-rate <br> pcierrors-high-completion_timeout-rate <br> pcierrors-high-replay_timer_timeout-rate <br>                                                      | PCIe serial number: xxx, location: 0000:??:01.1, devpath: /phys/!!:xxx pcie error, Error Types: '@@' are exceeding thresholds.                | xxx: random serial number / pathname <br> ??: possible location <br> !!: CPU0/1 / PE0 ~ 8 <br> @@: capitalize label name after "pcierrors-high-"      |
   | task-failed-with-non-zero-code-return-code                       | Task return code: 1.                                | Fixed message                                          |
   | load-hwinfo-fail                                                 | Failed to load hwinfos for PMBUS_ERROR_MONITOR monitor: NOT_FOUND: could not resolve to devpath              | Fixed message                                          |
   | error-monitor-procedural-error                                   | Test failed: INTERNAL: One of the monitors failed   | Fixed message                          |      
   | unknown-pcie-location                                            | PCIe location: '0000:??:01.7', is not found.        | ??: possible location                  |  

10. **Empty Failure Description**
    * Will include anything 

### Symptom Labels without matching issues 
>  *(19 labels with 30.85%)*
* **DIMM infos validation failure** - *14.4%*
* **no-host-console-output** - *3.06%*
* **Diorite location validation failure** - *1.67%*
* **pcierrors-high-lane_error-rate** - *1.41%*
* **HB16 firmware check Failed** - *1.35%*
* **Lower critical limit violated** - *1.2%*
* **ncsi_cable-preparation-error** - *1.12%*
* **Diorite Serial Number** - *0.84%*
* **Hardware config check failed** - *0.81%*
* **excessive-correctable-unclassified-cpu-errors** - *0.75%*
* **The fan count of Config_check_HW is not matched.** - *0.63%*
* **unknown-pcie-location** - *0.63%*
* **DMA stress test Failed** - *0.53%*
* **test-completion-missing-error-error_monitor** - *0.5%*
* **test-completion-missing-error-maxcorestim** - *0.47%*
* **HB16 location validation failure** - *0.41%*
* **DIMM location validation failure** - *0.39%*
* **Timeout exceeded.** - *0.38%*
* **test-completion-missing-error-fan_speed** - *0.3%*

### Symptom Labels with unique standard message but not all of the messages are match
> 9 labels with 24.61% while 22.54% are able to match
* **Diorite SSH Connection Failed** (*14.4%*)
  * Only one standard message (*14.28%*)
    * "Create Diorite SSH Connection failed.
      Can not connect to Diorite IP: 'fd00::4001:A9FF:FEFE:A9FB'"
    * *7%*
  * Rest of the Pattern Variations
    * Send command 'ip addr show net0; uptime' failed.
      Failure Info:
      Timeout opening channel....
    * Send command 'ls -l /sys/class/net | grep -e "eth0\|eth2\|eth4\|eth6"' failed.
      Failure Info:
      Exception message: 'NoneType' object has no attribute 'open_session'
      Traceback (most recent call last):
      File "/home/abmx/OpenTest.4011/Astoria.debug/custom/utils/sshconn.py", line 139, in send_ssh_cmd
         stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=timeout)
      File "/usr/local/lib/python3.7/dist-packages/paramiko/client.py", line 508, in exec_command
         chan = self._transport.open_session(timeout=timeout)
      AttributeError: 'NoneType' object has no attribute 'open_session'...
    * Send command '/usr/local/bin/gsys -k hardware parts' failed.
      Failure Info:
      SSH session not active...
    * Send command '/usr/local/bin/gsys -k hardware parts' failed.
      Failure Info:
      E0428 17:56:19.881042    1292 image_info.cc:147] Corrupt note in linux-vdso.so.1 at offset 88 type: 1 namesz: 330240 descsz: 6
      E0428 17:57:19.907466    1292 daemon_startup.cc:184] failure reading server version
      F0428 17:58:19.920459    1292 command.h:88] RPC platforms_gsys.EnumerateDevpaths failed with a DEADLINE_EXCEEDED error in 1m, terminating. Debug string for request: ()...
    * Send command '/usr/local/bin/gsys -k hardware parts' failed.
      Failure Info:
      Mismatched MAC...

* **Capture Diorite Console and Attach to log Failed** (*2.69%*)
  * Only one standard message (*2.51%*)
    * Caught Exception exception.
  * Rest of the Pattern Variations
    * Caught no_htool_usb_list exception.
      Exception message: No Diorite found under BMC via command 'htool usb list'.

* **test-completion-missing-error-memtester** (*2.52%*)
  * Only one standard message (*2.35%*)
    * Diag execution failed
  * Rest of the Pattern Variations
    * sh: line 1: /export/hda3/meltan/memtester/memtester: No such file or directory...
    * E0508 00:53:38.169011   17458 proto_cast_util.cc:587] CopyToFileDescriptorProto raised an error
      Type...

* **bad-bus** (*1.75%*)
  * Only one standard message (*1.24%*)
    * For local bus /phys/CPU0:device:nbio0.0:pcie_root@bridge:port1.1:\nexpected speed: 16.0GT/s, actual speed: 2.5GT/s
  * Rest of the Pattern Variations
    * For remote bus /phys/PE0/IO0:device:dna:lan:\nexpected width: 16, actual width: 8...

* **test-completion-missing-error-sat** (*1.12%*) 
  * Only one standard message (*1.11%*)
    * Diag execution failed.
  * Rest of the Pattern Variations
    * https://symbolize.corp.google.com/r/?trace=55c018cdeda5,
    * third_party/meltan/core/results/python/results.py:154: UserWarning: DEPRECATED: Construct a TestRun...

* **Check boot number Failed** (*0.81%*) 
  * Only one standard message (*0.31%*)
    * Send command '/usr/local/bin/gsys bootnum read' failed. Failure Info: Exception message: [Errno 104] Connection reset by peer
    * [ACON/Cycle = 2]: Check boot number Failed
  * Rest of the Pattern Variations
    * Send command '/usr/local/bin/gsys bootnum read' failed.
      Failure Info:
      Exception message: 
      Traceback ...
    * Send command '/usr/local/bin/gsys bootnum read' failed.
      Failure Info:
      Exception message: Timeout ope...
    * Boot num lower than expected.
      Current bootnum: 2, lower limit: 3...

* **Check Firmware Fail** (*0.63%*)
  * Only one standard message (*0.36%*)
    * MB CPLD version is Not get the version, but expect version should be  2.5.0.0...
  * Rest of the Pattern Variations
    * Check firmware fail : retry over 3 times !...
    * MB PowerSequencer version is , but expect version should be  7e d3 or e8 91...
    * MB CPLD version is 2.5.0.0, but expect version should be  2.5.0.3...
    * Check firmware fail : BMC CPLD version is Not get the version, but expect version should be  2.1.0.0...

* **CPU location validation failure** (*0.38%*)
  * Only one standard message (*0.26%*)
    * Component CPU SN: 9LS6995W20093_100-000000782 not found on unit
  * Rest of the Pattern Variations
    * Component CPU SN 9KZ9349N40064_100-000000782 location: CPU1, expected location: CPU0.

* **test-completion-missing-error-hwinterface_smoketest** (*0.31%*)
  * Only one standard message (*0.12%*)
    * Diag execution failed.
  * Rest of the Pattern Variations
    * sh: line 1: /export/hda3/meltan/hwinterface_smoketest/hwinterface_smoketest: No such file or directo



### Symptom Labels that have some standard messages are matched
> 7 labels with 21.61% while 17.94% are able to match
* **Checking BMC boot readiness and get BMC IP Failed** (*13.88%*)
  * Matched (*13.76%*)
      * Switch to agora console failed....
      * Failed to get IP address via telnet
         Response from command 'ip addr | grep global | grep eth1':
         ip addr | grep global | grep eth1
         root@roux:~#...
  * Unmatched
    * Caught EOFError exception.
      Exception message: telnet connection closed
    * Caught TimeoutError exception.
      Exception message: timed out
    * Caught OSError exception.
      Exception message: [Errno 113] No route to host
    * Create SSH connection to BMC failed
      Error reading SSH protocol banner...
    * Create SSH connection to BMC failed
      Error reading SSH protocol banner[Errno 104] Connection reset by peer...
    * Create SSH connection to BMC failed
      Unable to connect to 192.168.100.189: [Errno 110] Connection timed out...
    * Create SSH connection to BMC failed
      Unable to connect to 192.168.100.179: [Errno 113] No route to host...
    * Create SSH connection to BMC failed...
    * Caught ConnectionResetError exception.
      Exception message: [Errno 104] Connection reset by peer

* **The sensor count of Config_check_HW is not matched.** (*3.07%*)
  * Matched (*2.18%*)
    * Total number of sensors Expected: 224, Current: 223, device_id: , unit:  ---
      Missing:['MB OUTLET T 1,degrees C'] 
      Extra:[]...
    * Total number of sensors Expected: 176, Current: 175, device_id: , unit:  ---
      Missing:['MB OUTLET T 2,degrees C'] 
      Extra:[]...
    * Total number of sensors Expected: 176, Current: 175, device_id: , unit:  ---
      Missing:['MB OUTLET T 3,degrees C'] 
      Extra:[]...      
    * Total number of sensors Expected: 224, Current: 219, device_id: , unit:  ---
      Missing:['P48V VIN,volts', 'HOTSWAP PIN,watts', 'HOTSWAP T,degrees C', 'P48V IOUT,amps', 'HOTSWAP T,margin C'] 
      Extra:[]...
  * Unmatched
    * total number of sensors is not expected value:[136](actual:126)-----------
      Missing:['CPU0 P1V8,Volts;', 'CPU0 13V5,Volts;', 'CPU1 P1V8,Volts;', 'CPU1 13V5,Volts;', 'CPU0 P1V8 POUT,Watts;', 'CPU1 P1V8 POUT,Watts;', 'CPU0 P1V8 T,degrees C;', 'CPU1 P1V8 T,degrees C;', 'CPU0 P1V8 IOUT,Amps;', 'CPU1 P1V8 IOUT,Amps;']
      Extra:[]...
    * Total number of sensors Expected: 185, Current: 175, device_id: , unit:  ---
      Missing:['CPU0 P3V3,volts', 'CPU0 VDDIO,volts', 'CPU0 P3V3 POUT,watts', 'CPU0 VDDIO POUT,watts', 'CPU0 VIO T,degrees C', 'CPU0 P3V3 T,degrees C', 'CPU0 P3V3 IOUT,amps', 'CPU0 VDDIO IOUT,amps', 'CPU0 VIO T,margin C', 'CPU0 P3V3 T,margin C'] 
      Extra:[]...
    * total number of sensors is not expected value:[128](actual:127)-----------
      Missing:['CPU0 NBM T,degrees C;']
      Extra:[]...
    * Total number of sensors Expected: 185, Current: 159, device_id: , unit:  ---
      Missing:['CPU0 T,degrees C', 'DIMM0 T,degrees C', 'DIMM1 T,degrees C', 'DIMM2 T,degrees C', 'DIMM3 T,degrees C', 'DIMM4 T,degrees C', 'DIMM5 T,degrees C', 'DIMM6 T,degrees C', 'DIMM7 T,degrees C', 'DIMM8 T,degrees C', 'DIMM9 T,degrees C', 'DIMM10 T,degrees C', 'DIMM11 T,degrees C', 'CPU0 T,margin C', 'DIMM0 T,margin C', 'DIMM1 T,margin C', 'DIMM2 T,margin C', 'DIMM3 T,margin C', 'DIMM4 T,margin C', 'DIMM5 T,margin C', 'DIMM6 T,margin C', 'DIMM7 T,margin C', 'DIMM8 T,margin C', 'DIMM9 T,margin C', 'DIMM10 T,margin C', 'DIMM11 T,margin C'] 
      Extra:[]...
    * total number of sensors is not expected value:[128](actual:115)-----------
      Missing:['CPU1 T,degrees C;', 'DIMM12 T,degrees C;', 'DIMM13 T,degrees C;', 'DIMM14 T,degrees C;', 'DIMM15 T,degrees C;', 'DIMM16 T,degrees C;', 'DIMM17 T,degrees C;', 'DIMM18 T,degrees C;', 'DIMM19 T,degrees C;', 'DIMM20 T,degrees C;', 'DIMM21 T,degrees C;', 'DIMM22 T,degrees C;', 'DIMM23 T,degrees C;']
      Extra:[]...
    * Total number of sensors Expected: 185, Current: 183, device_id: , unit:  ---
      Missing:['CPU1 NBM T,degrees C', 'CPU1 NBM T,margin C'] 
      Extra:[]...
    * total number of sensors is not expected value:[136](actual:132)-----------
      Missing:['Habanero16_1,degrees C;', 'Habanero16_2,degrees C;', 'Habanero16_3,degrees C;', 'Habanero16_4,degrees C;']
      Extra:[]...
    * total number of sensors is not expected value:[136](actual:132)-----------
      Missing:['BRICK1 P12V,Volts;', 'BRICK1 P12V T,degrees C;', 'BRICK1 P12V POUT,Watts;', 'BRICK1 P12V IOUT,Amps;']
      Extra:[]...
    * total number of sensors is not expected value:[136](actual:132)-----------
      Missing:['BRICK2 P12V,Volts;', 'BRICK2 P12V T,degrees C;', 'BRICK2 P12V POUT,Watts;', 'BRICK2 P12V IOUT,Amps;']
      Extra:[]...
    * total number of sensors is not expected value:[128](actual:127)-----------
      Missing:['MB INLET T,degrees C;']
      Extra:[]...

* **Validate Diorite PN, SN and installed slot Failed** (*2.28%*)
  * Matched (*2.28%*)
    * Send command 'htool --usb_loc 1-1.1 target reset on' failed.
    * Send command 'htool --usb_loc 1-1.2 target reset on' failed.
    * Send command 'htool --usb_loc 1-1.7.1 target reset on' failed.
    * Send command 'htool --usb_loc 1-1.7.2 target reset on' failed.
  * Unmatched
    * Create SSH connection to '{}' failed.
      Error reading SSH protocol banner

* **Create Host SSH Connection failed** (*0.99%*)
  * Matched (*0.87%*)
    * Unable to connect to 192.168.200.57: [Errno 110] Connection timed out
    * [Errno -5] No address associated with hostname
  * Unmatched
    * Error reading SSH protocol banner
    * Authentication timeout.
    * [Errno -2] Name or service not known
  
* **Update Foxconn BIOS Failed** (*0.55%*)
  * Matched (*0.48%*)
      * Update BIOS failed.
         set the gpio 114 out 1...
         Flashing BIOS @/dev/mtd9
         Erasing block: 1/1024 (0%) 
      * Update BIOS failed.
         Exception message: 
         Traceback (most recent call last):
         File "/usr/lib/python3/
  * Unmatched
    * Update BIOS failed.
      It hits a timeout 3600 seconds after sending command
    * Parse response failure. Response:
      -------VERSION-------
      BMC                 : fbmc, local, 24.49.0.

**Total Sensors fail** (*0.54%*)
  * Matched (*0.37%*)
    * total number of sensors is not expected value:[136](actual:135)-----------
      Missing:['MB OUTLET T 1,degrees C;']
      Extra:[]
    * total number of sensors is not expected value:[136](actual:135)-----------
      Missing:['MB OUTLET T 2,degrees C;']
      Extra:[]
    * total number of sensors is not expected value:[136](actual:135)-----------
      Missing:['MB OUTLET T 3,degrees C;']
      Extra:[]
    * total number of sensors is not expected value:[136](actual:132)-----------
      Missing:['P48V VIN,Volts;', 'HOTSWAP PIN,Watts;', 'HOTSWAP T,degrees C;', 'P48V IOUT,Amps;']
      Extra:[]
  * Unmatched
    * total number of sensors is not expected value:[128](actual:127
      -----------
      Missing:['MB INLET T,degrees C;']
      Extra:[]
    * total number of sensors is not expected value:[136](actual:126)-----------
      Missing:['CPU0 P1V8,Volts;', 'CPU0 13V5,Volts;', 'CPU1 P1V8,Volts;', 'CPU1 13V5,Volts;', 'CPU0 P1V8 POUT,Watts;', 'CPU1 P1V8 POUT,Watts;', 'CPU0 P1V8 T,degrees C;', 'CPU1 P1V8 T,degrees C;', 'CPU0 P1V8 IOUT,Amps;', 'CPU1 P1V8 IOUT,Amps;']
      Extra:[]...
    * total number of sensors is not expected value:[128](actual:115)-----------
      Missing:['CPU1 T,degrees C;', 'DIMM12 T,degrees C;', 'DIMM13 T,degrees C;', 'DIMM14 T,degrees C;', 'DIMM15 T,degrees C;', 'DIMM16 T,degrees C;', 'DIMM17 T,degrees C;', 'DIMM18 T,degrees C;', 'DIMM19 T,degrees C;', 'DIMM20 T,degrees C;', 'DIMM21 T,degrees C;', 'DIMM22 T,degrees C;', 'DIMM23 T,degrees C;']
      Extra:[]...
    * total number of sensors is not expected value:[128](actual:127)-----------
      Missing:['CPU0 NBM T,degrees C;']
      Extra:[]...
    * total number of sensors is not expected value:[136](actual:132)-----------
      Missing:['Habanero16_1,degrees C;', 'Habanero16_2,degrees C;', 'Habanero16_3,degrees C;', 'Habanero16_4,degrees C;']
      Extra:[]...
    * total number of sensors is not expected value:[136](actual:136)-----------
      Missing:['Habanero16_1,degrees C;']
      Extra:['Habanero16_1,;']...
    * total number of sensors is not expected value:[136](actual:132)-----------
      Missing:['BRICK1 P12V,Volts;', 'BRICK1 P12V T,degrees C;', 'BRICK1 P12V POUT,Watts;', 'BRICK1 P12V IOUT,Amps;']
      Extra:[]...
    * total number of sensors is not expected value:[136](actual:132)-----------
      Missing:['BRICK2 P12V,Volts;', 'BRICK2 P12V T,degrees C;', 'BRICK2 P12V POUT,Watts;', 'BRICK2 P12V IOUT,Amps;']
      Extra:[]...
    * total number of sensors is not expected value:[128](actual:127)-----------
      Missing:['MB INLET T,degrees C;']
      Extra:[]...

* **Update Google BIOS Failed** (*0.3%*)
  * Matched (*0.28%*)
    * Send command '/export/hda3/meltan/biosintegrity/biosintegrity --expected_bios_version=""0.20230627.0-0""' failed.
      Failure Info:
    * Update BIOS failed.
      bios.bin
      bios.sig
  * Unmatched
    * Update BIOS failed.
      Usage: astoria_bios_updater.sh |VERSION|.....


### Labels without standard message patterns
* **FRU infos validation failure** (*3.14%*)

### Check database content
* **unknown-pcie-location**
   * No ACON in database
* **DMA stress test Failed**
  * No ACON in database

* **The sensor count of Config_check_HW is not matched.**
  * ACON cycle = 4 and cycle = 5
    * Missing *Total number of sensors Expected: 180, Current: 179, device_id: , unit:  --- Missing:['MB OUTLET T 3,degrees C'] Extra:[]*
  * ACON duplicate message

### Conclusion
* Currently, for top 90% labels, there will be around 71% can be auto-classified to the category and assigned suggesions


