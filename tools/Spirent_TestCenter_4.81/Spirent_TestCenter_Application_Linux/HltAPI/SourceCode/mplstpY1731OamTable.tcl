# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::mplstpOam:: {
}

set ::sth::mplstpOam::mplstpOamTable {
 ::sth::mplstpOam::


 { emulation_mplstp_y1731_oam_control
    { hname                       stcobj                     stcattr             type                                 priority      default      range     supported   dependency      mandatory   procfunc      mode       constants}
    { port_handle                 _none_                    _none_               ALPHANUM                                 1           _none_      _none_      true        _none_          false       _none_      _none_      _none_}
    { handle                      _none_                    _none_               ALPHANUM                                 2           _none_      _none_      true        _none_          false       _none_      _none_      _none_}
    { action                      _none_                    _none_               {CHOICES start stop delete}              5           _none_      _none_      true        _none_          true        _none_      _none_      _none_}
    { msg_type                    _none_                    _none_               {CHOICES cc lb lck ais tst csf dm lm stop_all} 3          _none_       _none_      true        _none_          false       _none_      _none_      _none_}
    { dm_tx_rate                 MplsTpOamDmCommandConfig   DmTxRate             {CHOICES dmrate_10_per_sec dmrate_1_per_sec dmrate_1_per_min dmrate_1_per_10min} \
                                                                                                                          6           _none_      _none_      true        {msg_type dm}   false       _none_      {start configDmCommand}      _none_}
    { dm_tx_type                 MplsTpOamDmCommandConfig   DmTxType             {CHOICES single_msg continuous}          6           _none_      _none_      true        {msg_type dm}   false       _none_      {start configDmCommand}      _none_}
    { csf_tx_type                MplsTpOamCsfCommandConfig  CsfTxType            {CHOICES single_msg continuous}          6           _none_      _none_      true        {msg_type csf}  false       _none_      {start configCsfCommand}     _none_}
    { csf_type                   MplsTpOamCsfCommandConfig  CsfType              {CHOICES los fdi_ais rdi dci}            6           _none_      _none_      true        {msg_type csf}  false       _none_      {start configCsfCommand}     _none_}
    { tst_tx_type                MplsTpOamTstCommandConfig  TstTxType            {CHOICES single_msg continuous}          6           _none_      _none_      true        {msg_type tst}  false       _none_      {start configTstCommand}     _none_}
    { lm_tx_rate                 MplsTpOamLmCommandConfig   LmTxRate             {CHOICES lmrate_10_per_sec lmrate_1_per_sec lmrate_1_per_min lmrate_1_per_10min}  \
                                                                                                                          6           _none_      _none_      true        {msg_type csf}  false       _none_      {start configLmCommand}     _none_}
    { lm_tx_type                 MplsTpOamLmCommandConfig   LmTxType             {CHOICES single_msg continuous}          6           _none_      _none_      true        {msg_type lm}   false       _none_      {start configLmCommand}     _none_}
    { lm_tx_fcf_mode             MplsTpOamLmCommandConfig   TxFCfMode            {CHOICES static step}                    6           _none_      _none_      true        {msg_type lm}   false       _none_      {start configLmCommand}     _none_}
    { lm_tx_fcf_step             MplsTpOamLmCommandConfig   TxFCfStep            NUMERIC                                  6           _none_      _none_      true        {msg_type lm}   false       _none_      {start configLmCommand}     _none_}
    { lm_tx_fcf_value            MplsTpOamLmCommandConfig   TxFCfValue           NUMERIC                                  6           _none_      _none_      true        {msg_type lm}   false       _none_      {start configLmCommand}     _none_}
    { lb_tx_type                 MplsTpOamLbCommandConfig   LbTxType             {CHOICES single_msg continuous}          6           _none_      _none_      true        {msg_type lb}   false       _none_      {start configLbCommand}     _none_}
    { lb_initial_transaction_id  MplsTpOamLbCommandConfig   InitialTransactionId NUMERIC                                  6           _none_      _none_      true        {msg_type lb}   false       _none_      {start configLbCommand}     _none_}
    { lb_meg_handle_list         _none_                     _none_               ANY                                      6           _none_      _none_      true        {msg_type lb}   false       _none_      _none_                      _none_}
 }                                                                                                                                                                                       
 { emulation_mplstp_y1731_oam_stats
    {hname                          stcobj                  stcattr         type                                    priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {port_handle                    _none_                  _none_         ALPHANUM                                    2               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {handle                         _none_                  _none_         ALPHANUM                                    2               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {mode                           _none_                  _none_         ANY                                         3               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 }
 { emulation_mplstp_y1731_oam_stats_cc
    {hname                               stcobj                        stcattr                         type         priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {ais_rx_state                      MplsTpOamCcLocalResults         AisRxState                     NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {cc_rx_count                       MplsTpOamCcLocalResults         CcRxCount                      NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {cc_tx_count                       MplsTpOamCcLocalResults         CcTxCount                      NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {dropped_pkt_count                 MplsTpOamCcLocalResults         DroppedPktCount                NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lck_rx_state                      MplsTpOamCcLocalResults         LckRxState                     NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {meg_id                            MplsTpOamCcLocalResults         MegId                          NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {mp_name                           MplsTpOamCcLocalResults         MpName                         NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_remote_meps                MplsTpOamCcLocalResults         NumOfRemoteMeps                NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_remote_meps_down           MplsTpOamCcLocalResults         NumOfRemoteMepsDown            NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_remote_meps_up             MplsTpOamCcLocalResults         NumOfRemoteMepsUp              NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_timeouts                   MplsTpOamCcLocalResults         NumOfTimeouts                  NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_unexpected_meg_ids         MplsTpOamCcLocalResults         NumOfUnexpectedMegIds          NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_unexpected_meg_levels      MplsTpOamCcLocalResults         NumOfUnexpectedMegLevels       NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_unexpected_meps            MplsTpOamCcLocalResults         NumOfUnexpectedMeps            NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_unexpected_period_values   MplsTpOamCcLocalResults         NumOfUnexpectedPeriodValues    NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {rdi_rx_state                      MplsTpOamCcLocalResults         RdiRxState                     NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {rdi_tx_state                      MplsTpOamCcLocalResults         RdiTxState                     NUMERIC          5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 }
  { emulation_mplstp_y1731_oam_stats_ais
    {hname                          stcobj                  stcattr         type                                    priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {ais_rx_count               MplsTpOamAisResults         AisRxCount       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {ais_rx_period              MplsTpOamAisResults         AisRxPeriod      NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {ais_rx_state               MplsTpOamAisResults         AisRxState       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {ais_tx_count               MplsTpOamAisResults         AisTxCount       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {ais_tx_state               MplsTpOamAisResults         AisTxState       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {meg_id                     MplsTpOamAisResults         MegId            NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {mp_name                    MplsTpOamAisResults         MpName           NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 }
  { emulation_mplstp_y1731_oam_stats_dm
    {hname                          stcobj                  stcattr           type                                    priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {dmm_rx_count               MplsTpOamDmResults         DmmRxCount       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {dmm_tx_count               MplsTpOamDmResults         DmmTxCount       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {dmr_rx_count               MplsTpOamDmResults         DmrRxCount       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {dmr_tx_count               MplsTpOamDmResults         DmrTxCount       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {meg_id                     MplsTpOamDmResults         MegId            NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {mp_name                    MplsTpOamDmResults         MpName           NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 }
  { emulation_mplstp_y1731_oam_stats_tst
    {hname                               stcobj                  stcattr         type                                  priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {last_seq_num_rx               MplsTpOamTstResults         LastSeqNumRx       NUMERIC                                  5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {last_seq_num_tx               MplsTpOamTstResults         LastSeqNumTx       NUMERIC                                  5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {meg_id                        MplsTpOamTstResults         MegId              NUMERIC                                  5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {mp_name                       MplsTpOamTstResults         MpName             NUMERIC                                  5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_out_of_seq                MplsTpOamTstResults         NumOutOfSeq        NUMERIC                                  5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {tst_rx_count                  MplsTpOamTstResults         TstRxCount         NUMERIC                                  5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {tst_tx_count                  MplsTpOamTstResults         TstTxCount         NUMERIC                                  5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 }
  { emulation_mplstp_y1731_oam_stats_csf
    {hname                       stcobj                stcattr         type                                    priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {meg_id                MplsTpOamCsfResults         MegId         NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {mp_name               MplsTpOamCsfResults         MpName        NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {rx_count              MplsTpOamCsfResults         RxCount       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {rx_csf_period         MplsTpOamCsfResults         RxCsfPeriod   NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {rx_csf_type           MplsTpOamCsfResults         RxCsfType     NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {tx_count              MplsTpOamCsfResults         TxCount       NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {tx_csf_type           MplsTpOamCsfResults         TxCsfType     NUMERIC                                     5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 }
  { emulation_mplstp_y1731_oam_stats_lb
    {hname                               stcobj                     stcattr                           type      priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {dropped_pkt_count                 MplsTpOamLbResults         DroppedPktCount                    NUMERIC       5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lbm_rx_count                      MplsTpOamLbResults         LbmRxCount                         NUMERIC       5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lbm_tx_count                      MplsTpOamLbResults         LbmTxCount                         NUMERIC       5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lbr_rx_count                      MplsTpOamLbResults         LbrRxCount                         NUMERIC       5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lbr_tx_count                      MplsTpOamLbResults         LbrTxCount                         NUMERIC       5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {meg_id                            MplsTpOamLbResults         MegId                              NUMERIC       5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {mp_name                           MplsTpOamLbResults         MpName                             NUMERIC       5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_timeouts                   MplsTpOamLbResults         NumOfTimeouts                      NUMERIC       5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_transaction_id_mismatches  MplsTpOamLbResults         NumOfTransactionIdMismatches       NUMERIC       5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 }
  { emulation_mplstp_y1731_oam_stats_lck
    {hname                            stcobj                  stcattr         type             priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {lck_rx_count              MplsTpOamLckResults         LckRxCount       NUMERIC              5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lck_rx_period             MplsTpOamLckResults         LckRxPeriod      NUMERIC              5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lck_rx_state              MplsTpOamLckResults         LckRxState       NUMERIC              5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lck_tx_count              MplsTpOamLckResults         LckTxCount       NUMERIC              5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lck_tx_state              MplsTpOamLckResults         LckTxState       NUMERIC              5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {meg_id                    MplsTpOamLckResults         MegId            NUMERIC              5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {mp_name                   MplsTpOamLckResults         MpName           NUMERIC              5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 } 
 { emulation_mplstp_y1731_oam_stats_lm
    {hname                               stcobj             stcattr             type           priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {lmm_rx_count              MplsTpOamLmResults         LmmRxCount           NUMERIC            5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lmm_tx_count              MplsTpOamLmResults         LmmTxCount           NUMERIC            5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lmr_rx_count              MplsTpOamLmResults         LmrRxCount           NUMERIC            5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {lmr_tx_count              MplsTpOamLmResults         LmrTxCount           NUMERIC            5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {meg_id                    MplsTpOamLmResults         MegId                NUMERIC            5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {mp_name                   MplsTpOamLmResults         MpName               NUMERIC            5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {tx_f_cf                   MplsTpOamLmResults         TxFCf                NUMERIC            5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 }
 { emulation_mplstp_y1731_oam_stats_meg
    {hname                                     stcobj                stcattr                      type                 priority          default       range           supported   dependency    mandatory   procfunc             mode          constants}
    {bad_cc_rx_count                    MplsTpOamMegResults         BadCcRxCount                 NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {cc_rx_state                        MplsTpOamMegResults         CcRxState                    NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {cc_tx_state                        MplsTpOamMegResults         CcTxState                    NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {dropped_pkt_count                  MplsTpOamMegResults         DroppedPktCount              NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {meg_id                             MplsTpOamMegResults         MegId                        NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {me_level                           MplsTpOamMegResults         MeLevel                      NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_meps                        MplsTpOamMegResults         NumOfMeps                    NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_timeouts                    MplsTpOamMegResults         NumOfTimeouts                NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_unexpected_meg_ids          MplsTpOamMegResults         NumOfUnexpectedMegIds        NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_unexpected_meg_levels       MplsTpOamMegResults         NumOfUnexpectedMegLevels     NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_unexpected_meps             MplsTpOamMegResults         NumOfUnexpectedMeps          NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {num_of_unexpected_period_values    MplsTpOamMegResults         NumOfUnexpectedPeriodValues  NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
    {port_name                          MplsTpOamMegResults         PortName                     NUMERIC                   5               _none_       _none_          true        _none_        false       _none_              _none_           _none_}
 }                                                   
}
