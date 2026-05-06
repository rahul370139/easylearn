-- TrainPI Supabase migration: interview_prep knowledge base
--
-- Run this once in the Supabase SQL editor for your project
-- (https://jlrywvqnhlqjslxfmbsr.supabase.co → SQL editor → New query → paste → Run).
--
-- After it succeeds, ingest the corpus locally:
--    cd backend && python -m rag_kb ingest /path/to/interview_prep
--
-- Re-ingestion is idempotent (chunk_hash is unique).

create extension if not exists vector;

create table if not exists interview_prep_kb (
  id            bigserial primary key,
  doc           text not null,
  section       text,
  chunk         text not null,
  chunk_hash    text not null unique,
  embedding     vector(384),                -- matches Cohere `embed-english-light-v3.0`
  created_at    timestamptz default now()
);

-- IVFFlat index for cosine-distance ANN search.
-- Tune `lists` ~= sqrt(rows). 100 is fine for a few-thousand-chunk corpus.
create index if not exists interview_prep_kb_embedding_idx
  on interview_prep_kb using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Server-side similarity search the backend calls via supabase-py rpc.
create or replace function match_interview_prep(
  query_embedding vector(384),
  match_count int default 6
)
returns table (id bigint, doc text, section text, chunk text, similarity float)
language sql stable
as $$
  select id, doc, section, chunk,
         1 - (embedding <=> query_embedding) as similarity
  from interview_prep_kb
  where embedding is not null
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- RLS posture
-- ------------------------------------------------------------------------
-- This table is reference content (interview_prep notes), not user data,
-- so we keep it simple for the demo: enable RLS, allow anon to read AND
-- write. Production-grade alternative: drop the write policy below and
-- ingest with SUPABASE_SERVICE_ROLE_KEY (which bypasses RLS).
alter table interview_prep_kb enable row level security;

drop policy if exists interview_prep_kb_read_all  on interview_prep_kb;
drop policy if exists interview_prep_kb_write_all on interview_prep_kb;

create policy interview_prep_kb_read_all
  on interview_prep_kb
  for select
  to anon, authenticated
  using (true);

create policy interview_prep_kb_write_all
  on interview_prep_kb
  for all
  to anon, authenticated
  using (true)
  with check (true);

-- Make the new RPC visible to the anon role used by the backend client.
grant execute on function match_interview_prep(vector, int) to anon, authenticated;
