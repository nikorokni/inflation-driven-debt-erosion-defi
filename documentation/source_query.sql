/*
Public BigQuery query published with Chaleenutthawut et al. (2024),
"Loan Portfolio Dataset From MakerDAO Blockchain Project."

This is the exact source query in the repository README. The current study did
not use a Dune Analytics query or Dune query ID.
*/

SELECT
        block_timestamp,
        block_number,
        transaction_index,
        trace_address,
        transaction_hash,
        input,
        ARRAY_TO_STRING(
                ARRAY(
                        SELECT CHR(CAST(num AS INT64))
                        FROM UNNEST(SPLIT(trace_address, ',')) AS num
                ),
                ","
        ) AS trace_addr_str
FROM `bigquery-public-data.crypto_ethereum.traces`
WHERE DATE(block_timestamp) >= "2019-11-12"
        AND trace_address IS NOT NULL
        AND call_type = "call"
        AND to_address = LOWER("0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B")
        AND status = 1
ORDER BY CAST(block_number AS INT64),
         CAST(transaction_index AS INT64),
         trace_addr_str;

