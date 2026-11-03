-- ころころおやつ（korokoro.html）のランキング用テーブルと関数
-- Supabase の SQL Editor にこのファイルをまるごと貼りつけて Run すれば準備完了です。
-- 何度実行しても壊れないように書いてあります（スコアと、あとから足したNGワードは残り、関数は上書き）。
--
-- しくみ：
--   ・ブラウザからはテーブルを直接読めない／書けない（RLSを有効にしてポリシーなし）。
--   ・下の4つの関数（rpc）だけを anon に公開し、NGワード・ありえないスコア・連投はすべてサーバー側で確認する。
--   ・1人（端末ごとのランダムなID）につき「いつもの」と「今日のチャレンジ（日本時間で日替わり）」で1行ずつ、自己ベストだけを残す。
--   ・IPアドレスはそのまま保存せず、日付つきでハッシュにしたもの（日ごとに変わる）だけを連投の判定に使う。
--
-- NGワードを足したいとき：
--   Supabase の Table Editor で korokoro_ng_words を開いて「Insert row」。
--     word  … 弾きたいことば（ひらがな・カタカナ・漢字・英字・数字どれでもOK。スペースや記号は無視されます）
--     match … part＝名前のどこかに入っていたら弾く ／ full＝名前全体がそのことばのときだけ弾く
--   短いことば（2〜3文字）や、ふつうの名前の一部になりやすいもの（例：かす→かすみ、shit→yoshitaka）は full にしてください。
--   足したことばは、もう載っている名前にもすぐ効きます（ランキングでは「ななしのおやつ」と表示）。
--   ズルっぽいスコアは Table Editor の korokoro_scores から行ごと消せます。

-- ===== テーブル =====
create table if not exists public.korokoro_ng_words (
  word  text primary key check (char_length(word) between 1 and 40),
  match text not null default 'part' check (match in ('part', 'full')),
  note  text
);

create table if not exists public.korokoro_scores (
  player      uuid        not null,
  board       text        not null check (board in ('all', 'daily')),
  day         date        not null,               -- 'all' は 2000-01-01 固定、'daily' は日本時間の日付
  name        text        not null check (char_length(name) between 1 and 10),
  score       int         not null check (score between 0 and 20000000),
  stage       int         not null check (stage between 1 and 999),
  combo       int         not null default 0,
  secs        int         not null default 0,
  author_hash text,
  updated_at  timestamptz not null default now(),
  primary key (player, board, day)
);
create index if not exists korokoro_scores_rank_idx on public.korokoro_scores(board, day, score desc, updated_at);

-- 送信の記録（連投よけ用。1日たったものは自動で消す）
create table if not exists public.korokoro_submits (
  author_hash text        not null,
  player      uuid        not null,
  at          timestamptz not null default now()
);
create index if not exists korokoro_submits_idx on public.korokoro_submits(author_hash, at);
create index if not exists korokoro_submits_player_idx on public.korokoro_submits(player, at);

alter table public.korokoro_ng_words enable row level security;
alter table public.korokoro_scores   enable row level security;
alter table public.korokoro_submits  enable row level security;
revoke all on public.korokoro_ng_words, public.korokoro_scores, public.korokoro_submits from anon, authenticated;

-- ===== 内部用：ことばを「くずした形」にそろえる =====
-- 1. 全角半角・大文字小文字をそろえる（NFKC）
-- 2. leet=true のときだけ、数字・記号を似た英字に戻す（sh1t→shit、f@ck→fack、5ex→sex）
-- 3. カタカナ→ひらがな、小さい字→大きい字（ぁ→あ、っ→つ）
-- 4. 英数字・ひらがな・漢字以外（スペース、記号、絵文字、伸ばし棒、見えない文字）を全部消す
-- 5. 同じ字の連続を1つにし、母音をのばしただけの字も消す（しいいね→しね、ねぇぇ→ね）
create or replace function public.korokoro_norm(p text, leet boolean default false) returns text
language plpgsql immutable set search_path = public as $$
declare s text := lower(normalize(coalesce(p, ''), NFKC));
begin
  if leet then
    s := translate(s, '013456789@$!|€£', 'oieasgtbgasilel');
  end if;
  s := translate(s,
    'ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶ',
    'ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔかけ');
  s := translate(s, 'ぁぃぅぇぉっゃゅょゎゕゖ', 'あいうえおつやゆよわかけ');
  s := regexp_replace(s, '[^a-z0-9ぁ-ゖ一-鿿㐀-䶿々〆]', '', 'g');
  s := regexp_replace(s, '(.)\1+', '\1', 'g');
  -- 母音をのばしただけの字を消す（しいね→しね、ばあか→ばか）
  s := regexp_replace(s, '([かがさざただなはばぱまやらわ])あ+', '\1', 'g');
  s := regexp_replace(s, '([きぎしじちぢにひびぴみり])い+', '\1', 'g');
  s := regexp_replace(s, '([くぐすずつづぬふぶぷむゆるゔ])う+', '\1', 'g');
  s := regexp_replace(s, '([けげせぜてでねへべぺめれ])え+', '\1', 'g');
  s := regexp_replace(s, '([こごそぞとどのほぼぽもよろを])お+', '\1', 'g');
  return s;
end $$;

-- NGワード表に、くずした形を自動でつける（Table Editor では読むだけの列になります）
alter table public.korokoro_ng_words add column if not exists norm_a text generated always as (public.korokoro_norm(word, false)) stored;
alter table public.korokoro_ng_words add column if not exists norm_b text generated always as (public.korokoro_norm(word, true)) stored;

-- ===== 内部用：名前として使えないか =====
-- 返り値 null ならOK、それ以外は理由
create or replace function public.korokoro_ng_reason(p text) returns text
language plpgsql stable set search_path = public as $$
declare
  raw text := lower(normalize(coalesce(p, ''), NFKC));
  a text := public.korokoro_norm(p, false);
  b text := public.korokoro_norm(p, true);
begin
  if raw ~ '(https?:|www\.|[a-z0-9-]+\.(com|net|org|jp|io|me|ly|gl|co|xyz|info|tv)(?![a-z0-9]))' then return 'link'; end if;
  if raw ~ '@[a-z0-9_]{2,}' then return 'handle'; end if;
  if exists (
    select 1 from public.korokoro_ng_words w
     where w.norm_a <> ''
       and ( (w.match = 'part' and (strpos(a, w.norm_a) > 0 or (w.norm_a !~ '[0-9]' and strpos(b, w.norm_b) > 0)))
          or (w.match = 'full' and (a = w.norm_a or (w.norm_a !~ '[0-9]' and b = w.norm_b))) )
  ) then return 'word'; end if;
  return null;
end $$;

-- 名前の前後の空白・改行・見えない文字を整える
create or replace function public.korokoro_clean_name(p text) returns text
language sql immutable set search_path = public as $$
  select btrim(regexp_replace(regexp_replace(normalize(coalesce(p, ''), NFC),
    '[[:cntrl:]\u200b-\u200f\u2028-\u202e\u2060-\u206f\ufeff]', '', 'g'), '\s+', ' ', 'g'))
$$;

-- ===== 公開1：名前が使えるか（ニックネーム入力のときに呼ぶ） =====
create or replace function public.korokoro_name_check(p_name text)
returns text
language plpgsql security definer stable set search_path = public as $$
declare n text := public.korokoro_clean_name(p_name);
begin
  if char_length(n) < 1 or char_length(n) > 10 then return 'length'; end if;
  return public.korokoro_ng_reason(n);
end $$;

-- ===== 公開2：スコアを送る =====
-- 返り値：その表での自分の順位・参加人数・自己ベスト
create or replace function public.korokoro_submit(
  p_player uuid, p_name text, p_daily boolean, p_score int, p_stage int, p_secs int, p_combo int default 0)
returns table(rank int, total int, best int)
language plpgsql security definer set search_path = public as $$
declare
  n   text := public.korokoro_clean_name(p_name);
  h   text := md5(coalesce(split_part(
           coalesce(nullif(current_setting('request.headers', true), ''), '{}')::json->>'x-forwarded-for', ',', 1), 'local')
           || ':' || current_date::text || ':picoruno-korokoro');
  bd  text := case when p_daily then 'daily' else 'all' end;
  dy  date := case when p_daily then (now() at time zone 'Asia/Tokyo')::date else date '2000-01-01' end;
  b   int;
  bx  text;
begin
  if p_player is null then raise exception 'korokoro_bad' using errcode = '22023'; end if;
  if char_length(n) < 1 or char_length(n) > 10 then raise exception 'korokoro_length' using errcode = '22023'; end if;
  if public.korokoro_ng_reason(n) is not null then raise exception 'korokoro_ng' using errcode = '22023'; end if;
  -- ありえないスコアを弾く（ゲーム内時間あたりの点・ステージの進み方・ステージクリアのボーナス分）
  if p_score is null or p_stage is null or p_secs is null
     or p_score < 0 or p_stage < 1 or p_secs < 5 or p_secs > 10800 or coalesce(p_combo, 0) < 0
     or p_score > p_secs * 6000 + 20000
     or p_stage > 1 + p_secs / 15
     or p_score < 500 * p_stage * (p_stage - 1)
     or coalesce(p_combo, 0) > p_secs * 3 + 10 then
    raise exception 'korokoro_bad' using errcode = '22023';
  end if;
  -- 連投よけ：同じ端末は8秒に1回、同じ回線は10分に30回まで
  if exists (select 1 from public.korokoro_submits s where s.player = p_player and s.at > now() - interval '8 seconds')
     or (select count(*) from public.korokoro_submits s where s.author_hash = h and s.at > now() - interval '10 minutes') >= 30 then
    raise exception 'korokoro_rate' using errcode = '22023';
  end if;
  insert into public.korokoro_submits(author_hash, player) values (h, p_player);
  if random() < 0.02 then delete from public.korokoro_submits where at < now() - interval '1 day'; end if;

  -- 今日のチャレンジの点は「いつもの」の自己ベストにも入る
  foreach bx in array case when p_daily then array['daily', 'all'] else array['all'] end loop
    insert into public.korokoro_scores as k (player, board, day, name, score, stage, combo, secs, author_hash)
    values (p_player, bx, case when bx = 'daily' then dy else date '2000-01-01' end, n, p_score, p_stage, coalesce(p_combo, 0), p_secs, h)
    on conflict (player, board, day) do update set
      name        = excluded.name,
      stage       = case when excluded.score > k.score then excluded.stage else k.stage end,
      combo       = case when excluded.score > k.score then excluded.combo else k.combo end,
      secs        = case when excluded.score > k.score then excluded.secs  else k.secs  end,
      author_hash = case when excluded.score > k.score then excluded.author_hash else k.author_hash end,
      updated_at  = case when excluded.score > k.score then now() else k.updated_at end,
      score       = greatest(k.score, excluded.score);
  end loop;
  -- 名前を変えたら、もう一方の表の名前もそろえる
  update public.korokoro_scores k set name = n where k.player = p_player and k.name <> n;

  select k.score into b from public.korokoro_scores k where k.player = p_player and k.board = bd and k.day = dy;
  return query
    select (1 + (select count(*) from public.korokoro_scores k where k.board = bd and k.day = dy and k.score > b))::int,
           (select count(*) from public.korokoro_scores k where k.board = bd and k.day = dy)::int,
           b;
end $$;

-- ===== 公開3：ランキングを見る =====
-- 上位 p_limit 人（最大100）＋ 圏外なら自分の行も最後につける。同じ点は同じ順位（先に出した人が上）。
create or replace function public.korokoro_top(p_daily boolean, p_player uuid default null, p_limit int default 50)
returns table(rank int, name text, score int, stage int, is_me boolean)
language sql security definer stable set search_path = public as $$
  with r as (
    select k.player, k.name, k.score, k.stage,
           rank()       over (order by k.score desc)               as rk,
           row_number() over (order by k.score desc, k.updated_at) as rn
      from public.korokoro_scores k
     where k.board = case when p_daily then 'daily' else 'all' end
       and k.day   = case when p_daily then (now() at time zone 'Asia/Tokyo')::date else date '2000-01-01' end
  )
  select r.rk::int,
         case when public.korokoro_ng_reason(r.name) is null then r.name else 'ななしのおやつ' end,
         r.score, r.stage, (p_player is not null and r.player = p_player)
    from r
   where r.rn <= least(greatest(coalesce(p_limit, 50), 1), 100)
      or (p_player is not null and r.player = p_player)
   order by r.rn
$$;

-- ===== 公開4：名前だけ変える =====
create or replace function public.korokoro_rename(p_player uuid, p_name text)
returns text
language plpgsql security definer set search_path = public as $$
declare n text := public.korokoro_clean_name(p_name);
begin
  if char_length(n) < 1 or char_length(n) > 10 then raise exception 'korokoro_length' using errcode = '22023'; end if;
  if public.korokoro_ng_reason(n) is not null then raise exception 'korokoro_ng' using errcode = '22023'; end if;
  update public.korokoro_scores set name = n where player = p_player;
  return n;
end $$;

revoke all on function public.korokoro_norm(text, boolean), public.korokoro_ng_reason(text), public.korokoro_clean_name(text) from public, anon, authenticated;
grant execute on function public.korokoro_name_check(text) to anon, authenticated;
grant execute on function public.korokoro_submit(uuid, text, boolean, int, int, int, int) to anon, authenticated;
grant execute on function public.korokoro_top(boolean, uuid, int) to anon, authenticated;
grant execute on function public.korokoro_rename(uuid, text) to anon, authenticated;

-- ===== NGワード（はじめの一覧） =====
-- ここにあることばは、何度 Run しても入れ直されます（白さんが Table Editor で消したものも戻るので、消したいときはこの一覧からも消してください）。
-- 人の名前（芸能人・実在の人）は入れていません。ふつうの名前が弾かれないように、名前の一部になりやすい短い語は full にしています。
insert into public.korokoro_ng_words(word, match, note) values
  -- 暴言・おどし
  ('死ね','part','暴言'),('氏ね','part','暴言'),('市ね','part','暴言'),('しね','full','暴言'),('しねよ','part','暴言'),('しねや','part','暴言'),
  ('しんでよ','part','暴言'),('しんどけ','part','暴言'),('ちね','full','暴言'),('タヒね','part','暴言'),('ころす','part','暴言'),('殺す','part','暴言'),
  ('ころせ','part','暴言'),('殺せ','part','暴言'),('ころしてやる','part','暴言'),('きえろ','part','暴言'),('消えろ','part','暴言'),
  ('くたばれ','part','暴言'),('じさつしろ','part','暴言'),('自殺しろ','part','暴言'),('首吊れ','part','暴言'),('くびつれ','part','暴言'),
  ('うざい','full','暴言'),('うぜえ','full','暴言'),('きもい','full','暴言'),('きもすぎ','part','暴言'),('きしょい','full','暴言'),
  ('ぶす','full','暴言'),('でぶ','full','暴言'),('はげ','full','暴言'),('ばか','full','暴言'),('ばかやろう','part','暴言'),('あほ','full','暴言'),
  ('かす','full','暴言'),('ごみ','full','暴言'),('くず','full','暴言'),('ごみくず','part','暴言'),('ざこ','full','暴言'),('うんこ','part','下品'),
  ('うんち','full','下品'),('くそ','full','下品'),('くそが','part','暴言'),('くそやろう','part','暴言'),('糞','part','下品'),
  -- 性的なことば
  ('ちんこ','part','性的'),('ちんぽ','part','性的'),('ちんちん','part','性的'),('ちんかす','part','性的'),('まんこ','part','性的'),('まんまん','part','性的'),
  ('おまんこ','part','性的'),('おっぱい','part','性的'),('ぱいぱん','part','性的'),('ちくび','part','性的'),('乳首','part','性的'),('きんたま','part','性的'),
  ('金玉','part','性的'),('せっくす','part','性的'),('えっち','full','性的'),('えろ','full','性的'),('えろい','part','性的'),('ふぇら','part','性的'),
  ('くんに','full','性的'),('れいぷ','part','性的'),('強姦','part','性的'),('ごうかん','full','性的'),('痴漢','part','性的'),('ちかん','full','性的'),
  ('おなにー','part','性的'),('オナニ','part','性的'),('しこしこ','part','性的'),('しこる','part','性的'),('精子','part','性的'),('精液','part','性的'),
  ('射精','part','性的'),('勃起','part','性的'),('ぼっき','part','性的'),('中出し','part','性的'),('なかだし','full','性的'),('童貞','part','性的'),
  ('処女','part','性的'),('やりまん','part','性的'),('やりちん','part','性的'),('ぱこぱこ','part','性的'),('あなる','part','性的'),('いく','full','性的'),
  ('いっちゃう','part','性的'),('ぜつりん','part','性的'),('絶倫','part','性的'),('淫乱','part','性的'),('いんらん','part','性的'),('変態','full','性的'),
  ('へんたい','full','性的'),('援交','part','性的'),('えんこう','full','性的'),('パパ活','part','性的'),('ぱぱかつ','part','性的'),('av女優','part','性的'),
  ('sex','full','性的'),('sexy','full','性的'),('porn','part','性的'),('penis','part','性的'),('vagina','part','性的'),('pussy','part','性的'),
  ('boobs','part','性的'),('tits','full','性的'),('cock','full','性的'),('dildo','part','性的'),('hentai','part','性的'),('blowjob','part','性的'),
  ('anal','full','性的'),('cum','full','性的'),('rape','full','性的'),('rapist','part','性的'),('chinko','part','性的'),('chinpo','part','性的'),
  ('manko','part','性的'),('oppai','part','性的'),('onani','part','性的'),
  -- 差別・ヘイト
  ('きちがい','part','差別'),('基地外','part','差別'),('気違い','part','差別'),('きちがえ','part','差別'),('がいじ','part','差別'),('まじきち','part','差別'),('害児','part','差別'),
  ('ちしょう','full','差別'),('めくら','part','差別'),('つんぼ','part','差別'),('おし','full','差別'),('かたわ','full','差別'),
  ('ちょん','full','差別'),('ちょんこ','part','差別'),('支那','part','差別'),('しなじん','part','差別'),('ちゃんころ','part','差別'),('黒んぼ','part','差別'),
  ('くろんぼ','part','差別'),('にがー','full','差別'),('ホモ','full','差別'),('ほもやろう','part','差別'),('おかま','full','差別'),('れず','full','差別'),
  ('部落','part','差別'),('穢多','part','差別'),('非人','part','差別'),('ざいにち','full','差別'),('土人','part','差別'),('どじん','full','差別'),
  ('nigger','part','差別'),('nigga','part','差別'),('faggot','part','差別'),('fag','full','差別'),('retard','part','差別'),('chink','full','差別'),
  ('nazi','full','差別'),('hitler','part','差別'),('ヒトラー','part','差別'),('ナチス','part','差別'),
  -- 英語の暴言
  ('fuck','part','暴言'),('fuk','full','暴言'),('fck','full','暴言'),('shit','full','暴言'),('bullshit','part','暴言'),('bitch','part','暴言'),
  ('cunt','part','暴言'),('asshole','part','暴言'),('motherfucker','part','暴言'),('kys','full','暴言'),('killyou','part','暴言'),('kill','full','暴言'),
  ('dieyou','part','暴言'),('godie','full','暴言'),('stfu','full','暴言'),('wtf','full','暴言'),
  ('korosu','part','暴言'),('kuso','full','暴言'),('unko','part','下品'),
  -- 薬物・犯罪
  ('覚醒剤','part','薬物'),('かくせいざい','part','薬物'),('しゃぶ','full','薬物'),('麻薬','part','薬物'),('大麻','full','薬物'),('たいま','full','薬物'),
  ('爆破予告','part','犯罪'),('殺害予告','part','犯罪'),('テロ','full','犯罪'),
  -- 淫夢語録
  ('淫夢','part','淫夢'),('いんむ','full','淫夢'),('114514','part','淫夢'),('1145141919810','part','淫夢'),('1919','part','淫夢'),('810','full','淫夢'),
  ('364364','part','淫夢'),('893','full','淫夢'),('野獣先輩','part','淫夢'),('やじゅうせんぱい','part','淫夢'),('野獣','full','淫夢'),('やじゅう','full','淫夢'),
  ('やりますねぇ','part','淫夢'),('やりますね','full','淫夢'),('いいよこいよ','part','淫夢'),('こいよ','full','淫夢'),('いいぞこれ','part','淫夢'),
  ('いきすぎ','part','淫夢'),('イキスギ','part','淫夢'),('いきますよいくいく','part','淫夢'),('いくいく','part','淫夢'),('んあっー','part','淫夢'),
  ('あーいいっすね','part','淫夢'),('ぬわあああん','part','淫夢'),('つかれたもおおん','part','淫夢'),('あくしろよ','part','淫夢'),('はえーよ','full','淫夢'),
  ('まずうちさぁ','part','淫夢'),('屋上あるんだけど','part','淫夢'),('おくじょうあるんだけど','part','淫夢'),('焼いてかない','part','淫夢'),('やいてかない','part','淫夢'),
  ('みとけよみとけよ','part','淫夢'),('見とけよ見とけよ','part','淫夢'),('あばれんなよ','part','淫夢'),('暴れんなよ','part','淫夢'),('ふぁっ','full','淫夢'),('あっー','full','淫夢'),
  ('ふぁーwww','full','淫夢'),('ほらほらほら','part','淫夢'),('おっすおねがいしまーす','part','淫夢'),('ありがとナス','part','淫夢'),('ありがとなす','part','淫夢'),
  ('王道を征く','part','淫夢'),('おうどうをいく','part','淫夢'),('24歳学生','part','淫夢'),('24さいがくせい','part','淫夢'),('ちゅっちゅ','full','淫夢'),
  ('きたない','full','淫夢'),('くさそう','full','淫夢'),('ひでぇ','full','淫夢'),('いいゾ～これ','part','淫夢'),('そうだよ','full','淫夢'),('せやな','full','淫夢'),
  ('ホモビ','part','淫夢'),('ほもび','part','淫夢'),('迫真','part','淫夢'),('はくしん','full','淫夢'),('空手部','part','淫夢'),('からてぶ','part','淫夢'),
  ('kmr','full','淫夢'),('mur','full','淫夢'),('tdn','full','淫夢'),('inmu','part','淫夢'),('yjsnpi','part','淫夢'),('ynsnpi','part','淫夢'),
  -- 運営になりすまし
  ('運営','part','なりすまし'),('うんえい','full','なりすまし'),('公式','part','なりすまし'),('こうしき','full','なりすまし'),('admin','part','なりすまし'),
  ('管理人','part','なりすまし')
on conflict (word) do update set match = excluded.match, note = excluded.note;
