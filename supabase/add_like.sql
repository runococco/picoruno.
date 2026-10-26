-- いいねを1つ増やす／減らす関数（Supabase の SQL Editor に貼って実行）
-- d は +1 / -1 だけを受けつけます（大きな数を送られても1つずつしか動かない）。
-- いいねの数は 0 より下にはなりません。
create or replace function public.add_like(g text, d integer)
returns integer
language sql
security definer
set search_path = public
as $$
  update game_stats
     set likes = greatest(0, likes + sign(coalesce(d, 0))::int)
   where game = g
  returning likes;
$$;

grant execute on function public.add_like(text, integer) to anon;
