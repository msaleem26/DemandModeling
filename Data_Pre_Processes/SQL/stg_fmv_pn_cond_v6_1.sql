with dp as (
  select
      pnm_auto_key
    , pcc_auto_key
    , value
    , date
    , count_data_points_pn_pc
    , exp_weight
    , w
    , confidence_pn_pc
    , max_date_pn_pc
    , nature
  from DW_PROD.STAGING.STG_FMV_RAW_v6_1
  where date > dateadd(day, -365 * 5, current_date)
    and pcc_auto_key in (1,2,67,5,4)
    and modded_z_score_pn_pc < 4
    and order_of_mag_pn_pc between 0.11 and 9.9
),

synthetic as
(
  select 
      pnm_auto_key
    , pcc_auto_key
    , estimated_fmv synth_fmv
  from dw_prod.staging.STG_FMV_FROM_RO_V6_1
),

pn_pc_index as (
    
select distinct 
      pnm_auto_key
    , pcc_auto_key
    from synthetic
    
    union 
      
    select distinct 
      pnm_auto_key
    , pcc_auto_key
    from dp
    
    ),


fmv as (
  select
    pnm.pn
  , pcc.condition_code
  , pn_pc_index.pnm_auto_key
  , pn_pc_index.pcc_auto_key
  , count_data_points_pn_pc
  , max_date_pn_pc latest_data_point_date_pn_pc
  , confidence_pn_pc
  , case
      when sum(w * exp_weight) != 0 then round(sum(value * w * exp_weight) / sum(w * exp_weight),2)
    end exp_fmv
  , synth_fmv
    
  from pn_pc_index

  left join dp on dp.pnm_auto_key = pn_pc_index.pnm_auto_key and dp.pcc_auto_key = pn_pc_index.pcc_auto_key
  left join synthetic on synthetic.pnm_auto_key = pn_pc_index.pnm_auto_key and synthetic.pcc_auto_key = pn_pc_index.pcc_auto_key

  left join CLA_PROD.QUANTUM_PROD_QCTL.parts_master pnm
   on to_number(pn_pc_index.pnm_auto_key) = to_number(pnm.pnm_auto_key)

  left join CLA_PROD.QUANTUM_PROD_QCTL.part_condition_codes pcc
   on to_number(pn_pc_index.pcc_auto_key) = to_number(pcc.pcc_auto_key)

  group by
   all
   )

select
    pn
  , condition_code
  , pnm_auto_key
  , pcc_auto_key
  , count_data_points_pn_pc
  , latest_data_point_date_pn_pc
  , exp_fmv natty_fmv
  , synth_fmv
  , case when exp_fmv is null then synth_fmv else exp_fmv end fmv
  , case when exp_fmv is null then 'F' else confidence_pn_pc end confidence_pn_pc
  , case when exp_fmv is null then 'synth' else 'natty' end fmv_source
  
from fmv
--where synth_fmv is not null 