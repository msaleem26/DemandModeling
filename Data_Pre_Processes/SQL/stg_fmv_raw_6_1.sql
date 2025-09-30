with 



all_points_pre as (
  
select
  'FGI' source
, 'HUMAN' nature
, -1 source_key
, pnm.pnm_auto_key
, 5 pcc_auto_key
, fgi.unit_price value
, price_date date
from cla_prod.manual_tables.fgi_prices fgi
left join cla_prod.quantum_prod_qctl.parts_master pnm
  on pnm.pn = fgi.part_number
 and pnm._fivetran_deleted = False
 and pnm.active_part = 'T'
      
  UNION ALL 

select * EXCLUDE row_num
from (
  select
      'SO' source
    , 'HUMAN' nature
    , sod_auto_key source_key
    , pnm_auto_key
    , pcc_auto_key
    , unit_price value
    , entry_date date
    , row_number() over (partition by pnm_auto_key, pcc_auto_key, entry_date, unit_price order by sod_auto_key asc) row_num
  from ${ev_cla_database}.${ev_cla_qctl_schema}.SO_DETAIL sod
  inner join (select 
      soh_auto_key
    , count(*) so_len
    from ${ev_cla_database}.${ev_cla_qctl_schema}.so_detail
    where _fivetran_deleted = false
    group by soh_auto_key ) so_len on so_len.soh_auto_key = sod.soh_auto_key
  where entry_date <= current_date()
    and route_code = 'S'
    and unit_price > 1
    and qty_invoiced  > 0
    and _fivetran_deleted = false
    and so_len.so_len < 40
    and sod.soh_auto_key not in (select distinct soh_auto_key
                             from ${ev_cla_database}.${ev_cla_qctl_schema}.SO_DETAIL
                             where route_code = 'E') -- we don't want to bring Exchange Outright Conversions
    )
WHERE row_num = 1

  UNION ALL

select * EXCLUDE row_num
from (
  select 
    'PO' source
  , 'HUMAN' nature
  , pod_auto_key source_key 
  , PNM_AUTO_KEY
  , PCC_AUTO_KEY
  , UNIT_COST * ${jv_margin} value
  , entry_date date
  , row_number() over (partition by pnm_auto_key, pcc_auto_key, entry_date, unit_cost order by pod_auto_key asc) row_num
  from ${ev_cla_database}.${ev_cla_qctl_schema}.PO_DETAIL 
  where entry_date <= current_date()
  and unit_cost > 1
  and QTY_ORDERED  > 0 
  and route_code = 'P'
  and _fivetran_deleted = false)
where row_num = 1 

  UNION ALL

select * EXCLUDE row_num
from (


  select distinct
    'VQ' source
  , 'HUMAN' nature
  , vqd_auto_key source_key
  , PNM_AUTO_KEY
  , PCC_AUTO_KEY
  , UNIT_COST value
  , entry_date date
    , row_number() over (partition by pnm_auto_key, pcc_auto_key, entry_date, unit_cost order by vqd_auto_key asc) row_num
  from ${ev_cla_database}.${ev_cla_qctl_schema}.VQ_DETAIL  
  left join dw_prod.staging.STG_CMP_PRICING_SCORE score
    on VQ_DETAIL.cmp_auto_key = score.cmp_auto_key
  where entry_date <= current_date()
  and unit_cost > 1
  and QTY_QUOTED  > 0 
  and route_code = 'S'
  and abs(coalesce(score.gap, 0)) < 50 -- filter out companies that quote crazy high
  and _fivetran_deleted = false)
where row_num = 1
),


all_points as (
    select *
    from all_points_pre
--    union all
--    select * 
--    from ar_replicants
--    union all
--    select * 
--    from sv_replicants
--    union all
--    select * 
--    from oh_replicants
),

points as (
  select
    all_points.*
  , to_char(pnm.IC_UDF_001) pn_tier
  from all_points
  left join ${ev_cla_database}.${ev_cla_qctl_schema}.parts_master pnm
    on pnm.pnm_auto_key = all_points.pnm_auto_key
  where date > dateadd(day, -${jv_dr}, current_date)

),

last_point_date_pn_pc as (
  select 
    PNM_AUTO_KEY
  , PCC_AUTO_KEY
  , max(points.date) max_date
  from points
  where nature = 'HUMAN' and source = 'VQ'
  group by PNM_AUTO_KEY
         , PCC_AUTO_KEY

),

last_point_date_pn as (
  select 
    PNM_AUTO_KEY
  , max(points.date) max_date
  from points
  where nature = 'HUMAN' and source = 'VQ'
  group by PNM_AUTO_KEY
),

-- full data set stats
-- change on V6: take VQ data only
stats_pn_pc as (
  SELECT
    avg(value)    average_pn_pc
  , stddev(value) std_dev_pn_pc
  , median(value) median_pn_pc
  , count(value) count_data_points_pn_pc
  , pnm_auto_key
  , pcc_auto_key
  from points
  where source = 'VQ'
  group by pnm_auto_key, pcc_auto_key
),

stats_pn as (
  SELECT
    avg(value)    average_pn
  , stddev(value) std_dev_pn
  , median(value) median_pn
  , count(value) count_data_points_pn
  , pnm_auto_key
  from points
  where source = 'VQ'
  group by pnm_auto_key
),

-- short window stats
stats_pn_pc_window as (
  SELECT
    avg(value)    average_pn_pc_window
  , stddev(value) std_dev_pn_pc_window
  , median(value) median_pn_pc_window
  , count(value) count_data_points_pn_pc_window
  , pnm_auto_key
  , pcc_auto_key
  from points
  where 

  points.date >
    case
      when points.pn_tier = '1' then dateadd(day, -${jv_dr_tier_one}, current_date)
      else  dateadd(day, -${jv_dr_other}, current_date)
    end
  group by pnm_auto_key, pcc_auto_key
),

stats_pn_window as (
  SELECT
    avg(value)    average_pn_window
  , stddev(value) std_dev_pn_window
  , median(value) median_pn_window
  , count(value) count_data_points_pn_window
  , pnm_auto_key
  from points

  where 

  points.date >
    case
      when points.pn_tier = '1' then dateadd(day, -${jv_dr_tier_one}, current_date)
      else  dateadd(day, -${jv_dr_other}, current_date)
    end
  group by pnm_auto_key
),


final as (
  select 
    points.*
  , stats_pn_pc.median_pn_pc
  , stats_pn_pc.average_pn_pc
  , stats_pn_pc.std_dev_pn_pc
  , stats_pn_pc_window.median_pn_pc_window
  , case when coalesce(stats_pn_pc.median_pn_pc,0) <> 0 then value / stats_pn_pc.median_pn_pc end order_of_mag_pn_pc
  , stats_pn_pc.count_data_points_pn_pc
  , abs(points.value - stats_pn_pc_window.median_pn_pc_window) mad_pn_pc
  , case when stats_pn_pc.std_dev_pn_pc <> 0 then abs((points.value - stats_pn_pc.average_pn_pc) / stats_pn_pc.std_dev_pn_pc) end z_score_pn_pc
  , stats_pn.median_pn
  , stats_pn.average_pn
  , stats_pn.std_dev_pn
  , stats_pn_window.median_pn_window
  , case when coalesce(stats_pn.median_pn,0) <> 0 then value / stats_pn.median_pn end order_of_mag_pn
  , stats_pn.count_data_points_pn
  , abs(points.value - stats_pn_window.median_pn_window) mad_pn
  , case when stats_pn.std_dev_pn <> 0 then abs((points.value - stats_pn.average_pn) / stats_pn.std_dev_pn) end z_score_pn

  from points

  left join stats_pn_pc
    on stats_pn_pc.pnm_auto_key = points.pnm_auto_key
   and stats_pn_pc.pcc_auto_key = points.pcc_auto_key
  
  left join stats_pn
    on stats_pn.pnm_auto_key = points.pnm_auto_key

  left join stats_pn_pc_window
    on stats_pn_pc_window.pnm_auto_key = points.pnm_auto_key
   and stats_pn_pc_window.pcc_auto_key = points.pcc_auto_key
  
  left join stats_pn_window
    on stats_pn_window.pnm_auto_key = points.pnm_auto_key
  ),

  
mad_pn_pc as -- calculate only for last n months
(
  select 
  
    final.pnm_auto_key
  , final.pcc_auto_key
  , median(abs(final.value - stats_pn_pc_window.median_pn_pc_window)) mad_pn_pc
  
  from final 

  left join stats_pn_pc_window
    on stats_pn_pc_window.pnm_auto_key = final.pnm_auto_key
   and stats_pn_pc_window.pcc_auto_key = final.pcc_auto_key

  where 

  final.date >
    case
      when final.pn_tier = '1' then dateadd(day, -${jv_dr_tier_one}, current_date)
      else  dateadd(day, -${jv_dr_other}, current_date)
    end
      
  group by final.pnm_auto_key
        , final.pcc_auto_key
),

mad_pn as
(
  select 
  
    final.pnm_auto_key
  , median(abs(final.value - stats_pn_window.median_pn_window)) mad_pn
  
  from final 
  
  left join stats_pn_window
    on stats_pn_window.pnm_auto_key = final.pnm_auto_key

  where final.date >
    case
      when final.pn_tier = '1' then dateadd(day, -${jv_dr_tier_one}, current_date)
      else  dateadd(day, -${jv_dr_other}, current_date) end

 group by final.pnm_auto_key
),

final_w as (
  select 
    source
  , nature
  , source_key
  , final.pn_tier
  , final.pnm_auto_key
  , final.pcc_auto_key
  , case
      when source='VQ' then ${jv_w_vq}
      -- when source='CQ' then ${jv_w_cq}
      when source='PO' then ${jv_w_po}
      when source='SO' then ${jv_w_so}
      when source='REPAIR_VQ' then ${jv_w_repair_vq}
      when source='FGI' then ${jv_w_fgi}
    else 1
  end w
  , value
  , final.date
  , median_pn_pc
  , median_pn_pc_window
  , std_dev_pn_pc 
  , average_pn_pc
  , order_of_mag_pn_pc
  , count_data_points_pn_pc
  , z_score_pn_pc
  , case
    when mad_pn_pc.mad_pn_pc <> 0 
      then  0.6745 * (abs(value - median_pn_pc_window))
      / mad_pn_pc.mad_pn_pc
   end modded_z_score_pn_pc

  , case
      when final.pn_tier = '1' then iff(date > dateadd(day, -${jv_dr_tier_one}, current_date), true, false)
      else  iff(date > dateadd(day, -${jv_dr_other}, current_date), true, false)
    end is_in_mod_z_date_range

  , median_pn
  , median_pn_window
  , std_dev_pn
  , average_pn
  , order_of_mag_pn
  , count_data_points_pn
  , z_score_pn
  , case when mad_pn.mad_pn <> 0
      then  0.6745 * (abs(value - median_pn_window))
      / mad_pn.mad_pn
    end modded_z_score_pn
  , last_point_date_pn_pc.max_date max_date_pn_pc
  , last_point_date_pn.max_date max_date_pn

  from final

  left join mad_pn_pc
    on final.pnm_auto_key = mad_pn_pc.pnm_auto_key
    and final.pcc_auto_key = mad_pn_pc.pcc_auto_key

  left join mad_pn
    on final.pnm_auto_key = mad_pn.pnm_auto_key

  left join last_point_date_pn_pc
    on final.pnm_auto_key = last_point_date_pn_pc.pnm_auto_key
    and final.pcc_auto_key = last_point_date_pn_pc.pcc_auto_key

  left join last_point_date_pn
    on final.pnm_auto_key = last_point_date_pn.pnm_auto_key
      
),

final_ww as (
  select *
  , case
      when pn_tier = '1'
    then 
   ${jv_dr} * exp(-${jv_k_tier_one} * datediff(day, date, current_date)) 
      - datediff(day,date, current_date) * exp(-${jv_k_tier_one}*${jv_dr}) 
  else

    ${jv_dr} * exp(-${jv_k_other} * datediff(day, date, current_date)) 
      - datediff(day,date, current_date) * exp(-${jv_k_other}*${jv_dr}) 

  end exp_weight
  from final_w
  )

select 
    source
  , nature
  , source_key
  , pnm.pnm_auto_key
  , pcc.pcc_auto_key
  , pnm.pn
  , pcc.condition_code
  , value
  , date
  , median_pn_pc
  , median_pn_pc_window
  , order_of_mag_pn_pc
  , is_in_mod_z_date_range
  , coalesce(z_score_pn_pc, 0) z_score_pn_pc
  , iff(is_in_mod_z_date_range=true,coalesce(modded_z_score_pn_pc, 0),0) modded_z_score_pn_pc
  , count_data_points_pn_pc
  , median_pn
  , median_pn_window
  , order_of_mag_pn
  , coalesce(z_score_pn, 0) z_score_pn
  , iff(is_in_mod_z_date_range=true,coalesce(modded_z_score_pn, 0),0) modded_z_score_pn
  , count_data_points_pn
  , case when exp_weight < 0 then 0 else exp_weight end exp_weight
  , w
  , max_date_pn_pc
  , max_date_pn
  
  , CASE
      WHEN count_data_points_pn_pc >= 5 THEN
        CASE
          WHEN datediff(month, max_date_pn_pc, current_date) <= 2 THEN
            CASE
              WHEN std_dev_pn_pc / average_pn_pc <= 0.075 THEN 'A'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.17 THEN 'B'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.29 THEN 'C'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn_pc, current_date) <= 9 THEN
            CASE
              WHEN std_dev_pn_pc / average_pn_pc <= 0.17 THEN 'B'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.29 THEN 'C'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn_pc, current_date) <= 14 THEN
            CASE
              WHEN std_dev_pn_pc / average_pn_pc <= 0.29 THEN 'C'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn_pc, current_date) <= 24 THEN
            CASE
              WHEN std_dev_pn_pc / average_pn_pc <= 0.47 THEN 'D'
              ELSE 'F'
            END
          ELSE 'F'
        END

      WHEN count_data_points_pn_pc >= 3 THEN
        CASE
          WHEN datediff(month, max_date_pn_pc, current_date) <= 9 THEN
            CASE
              WHEN std_dev_pn_pc / average_pn_pc <= 0.17 THEN 'B'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.29 THEN 'C'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn_pc, current_date) <= 14 THEN
            CASE
              WHEN std_dev_pn_pc / average_pn_pc <= 0.29 THEN 'C'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn_pc, current_date) <= 24 THEN
            CASE
              WHEN std_dev_pn_pc / average_pn_pc <= 0.47 THEN 'D'
              ELSE 'F'
            END
          ELSE 'F'
        END

      WHEN count_data_points_pn_pc = 2 THEN
        CASE
          WHEN datediff(month, max_date_pn_pc, current_date) <= 14 THEN
            CASE
              WHEN std_dev_pn_pc / average_pn_pc <= 0.29 THEN 'C'
              WHEN std_dev_pn_pc / average_pn_pc <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn_pc, current_date) <= 24 THEN
            CASE
              WHEN std_dev_pn_pc / average_pn_pc <= 0.47 THEN 'D'
              ELSE 'F'
            END
          ELSE 'F'
        END

      ELSE 'F'
    END AS confidence_pn_pc


    
    , CASE
      WHEN count_data_points_pn >= 5 THEN
        CASE
          WHEN datediff(month, max_date_pn, current_date) <= 2 THEN
            CASE
              WHEN std_dev_pn / average_pn <= 0.075 THEN 'A'
              WHEN std_dev_pn / average_pn <= 0.17 THEN 'B'
              WHEN std_dev_pn / average_pn <= 0.29 THEN 'C'
              WHEN std_dev_pn / average_pn <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn, current_date) <= 9 THEN
            CASE
              WHEN std_dev_pn / average_pn <= 0.17 THEN 'B'
              WHEN std_dev_pn / average_pn <= 0.29 THEN 'C'
              WHEN std_dev_pn / average_pn <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn, current_date) <= 14 THEN
            CASE
              WHEN std_dev_pn / average_pn <= 0.29 THEN 'C'
              WHEN std_dev_pn / average_pn <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn, current_date) <= 24 THEN
            CASE
              WHEN std_dev_pn / average_pn <= 0.47 THEN 'D'
              ELSE 'F'
            END
          ELSE 'F'
        END

      WHEN count_data_points_pn >= 3 THEN
        CASE
          WHEN datediff(month, max_date_pn, current_date) <= 9 THEN
            CASE
              WHEN std_dev_pn / average_pn <= 0.17 THEN 'B'
              WHEN std_dev_pn / average_pn <= 0.29 THEN 'C'
              WHEN std_dev_pn / average_pn <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn, current_date) <= 14 THEN
            CASE
              WHEN std_dev_pn / average_pn <= 0.29 THEN 'C'
              WHEN std_dev_pn / average_pn <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn, current_date) <= 24 THEN
            CASE
              WHEN std_dev_pn / average_pn <= 0.47 THEN 'D'
              ELSE 'F'
            END
          ELSE 'F'
        END

      WHEN count_data_points_pn = 2 THEN
        CASE
          WHEN datediff(month, max_date_pn, current_date) <= 14 THEN
            CASE
              WHEN std_dev_pn / average_pn <= 0.29 THEN 'C'
              WHEN std_dev_pn / average_pn <= 0.47 THEN 'D'
              ELSE 'F'
            END
          WHEN datediff(month, max_date_pn, current_date) <= 24 THEN
            CASE
              WHEN std_dev_pn / average_pn <= 0.47 THEN 'D'
              ELSE 'F'
            END
          ELSE 'F'
        END

      ELSE 'F'
    END AS confidence_pn
    
  , case
      when abs(iff(is_in_mod_z_date_range=true,coalesce(modded_z_score_pn_pc, 0),0)) >= 4 then 'outlier'
    end modded_z_score_outlier_pn_pc
  , case
      when order_of_mag_pn_pc >= 9.9
        or order_of_mag_pn_pc <= 0.11 then 'outlier'
    end order_of_mag_outlier_pn_pc
  
from final_ww
left join cla_prod.quantum_prod_qctl.parts_master pnm
  on pnm.pnm_auto_key = final_ww.pnm_auto_key
left join cla_prod.quantum_prod_qctl.part_condition_codes pcc
  on pcc.pcc_auto_key = final_ww.pcc_auto_key
    
  