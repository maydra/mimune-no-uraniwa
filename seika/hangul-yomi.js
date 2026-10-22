/* seika/hangul-yomi.js — ハングルの語を、発音どおりのカタカナとローマ字にする。
   _tools/seika/hangul_kana.py をそのまま移したもの（規則を変えたら両方を直し、
   _tools/seika/check_yomi_js.py で全曲の語の結果が同じか確かめる）。
   読みを付ける道具（yomi.html）が使う。 */
(function (root) {
    'use strict';

    var CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'.split('');
    var JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'.split('');
    var JONG = [''].concat('ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ'.split(''));

    var VOWEL = {
        'ㅏ': 'a', 'ㅐ': 'e', 'ㅑ': 'ya', 'ㅒ': 'ye', 'ㅓ': 'o', 'ㅔ': 'e',
        'ㅕ': 'yo', 'ㅖ': 'ye', 'ㅗ': 'o', 'ㅘ': 'wa', 'ㅙ': 'we', 'ㅚ': 'we',
        'ㅛ': 'yo', 'ㅜ': 'u', 'ㅝ': 'wo', 'ㅞ': 'we', 'ㅟ': 'wi', 'ㅠ': 'yu',
        'ㅡ': 'u', 'ㅢ': 'ui', 'ㅣ': 'i'
    };
    var COLS = ['a', 'e', 'ya', 'ye', 'o', 'wa', 'we', 'yo', 'u', 'wo', 'wi', 'yu', 'ui', 'i'];
    var ROWS = {
        '':   'ア エ ヤ イェ オ ワ ウェ ヨ ウ ウォ ウィ ユ ウィ イ',
        'k':  'カ ケ キャ キェ コ クァ クェ キョ ク クォ クィ キュ クィ キ',
        'g':  'ガ ゲ ギャ ギェ ゴ グァ グェ ギョ グ グォ グィ ギュ グィ ギ',
        'n':  'ナ ネ ニャ ニェ ノ ヌァ ヌェ ニョ ヌ ヌォ ヌィ ニュ ヌィ ニ',
        't':  'タ テ テャ テェ ト トァ トェ ティョ トゥ トゥォ トゥィ テュ トゥィ ティ',
        'd':  'ダ デ デャ デェ ド ドァ ドェ ディョ ドゥ ドゥォ ドゥィ デュ ドゥィ ディ',
        'r':  'ラ レ リャ リェ ロ ルァ ルェ リョ ル ルォ ルィ リュ ルィ リ',
        'm':  'マ メ ミャ ミェ モ ムァ ムェ ミョ ム ムォ ムィ ミュ ムィ ミ',
        'p':  'パ ペ ピャ ピェ ポ プァ プェ ピョ プ プォ プィ ピュ プィ ピ',
        'b':  'バ ベ ビャ ビェ ボ ブァ ブェ ビョ ブ ブォ ブィ ビュ ブィ ビ',
        's':  'サ セ シャ シェ ソ スァ スェ ショ ス スォ シュィ シュ スィ シ',
        'ch': 'チャ チェ チャ チェ チョ チュァ チュェ チョ チュ チュォ チュィ チュ チュィ チ',
        'j':  'ジャ ジェ ジャ ジェ ジョ ジュァ ジュェ ジョ ジュ ジュォ ジュィ ジュ ジュィ ジ',
        'h':  'ハ ヘ ヒャ ヒェ ホ ファ フェ ヒョ フ フォ フィ ヒュ フィ ヒ'
    };
    var TABLE = {};
    Object.keys(ROWS).forEach(function (row) {
        var kana = ROWS[row].split(' ');
        TABLE[row] = {};
        COLS.forEach(function (c, i) { TABLE[row][c] = kana[i]; });
    });

    var FINAL_KANA = { '': '', 'ㄱ': 'ㇰ', 'ㄴ': 'ン', 'ㄷ': 'ッ', 'ㄹ': 'ㇽ', 'ㅁ': 'ㇺ', 'ㅂ': 'ㇷ゚', 'ㅇ': 'ン' };
    var ROW_OF = {
        'ㄱ': ['k', 'g'], 'ㄷ': ['t', 'd'], 'ㅂ': ['p', 'b'], 'ㅈ': ['ch', 'j'],
        'ㄲ': ['k', null], 'ㄸ': ['t', null], 'ㅃ': ['p', null], 'ㅉ': ['ch', null], 'ㅆ': ['s', null],
        'ㅋ': ['k', null], 'ㅌ': ['t', null], 'ㅍ': ['p', null], 'ㅊ': ['ch', null],
        'ㄴ': ['n', null], 'ㄹ': ['r', null], 'ㅁ': ['m', null], 'ㅅ': ['s', null],
        'ㅎ': ['h', null], 'ㅇ': ['', null]
    };
    var TENSE = { 'ㄱ': 'ㄲ', 'ㄷ': 'ㄸ', 'ㅂ': 'ㅃ', 'ㅅ': 'ㅆ', 'ㅈ': 'ㅉ' };
    var ASPIRATE = { 'ㄱ': 'ㅋ', 'ㄷ': 'ㅌ', 'ㅂ': 'ㅍ', 'ㅈ': 'ㅊ' };
    var NASAL = { 'ㄱ': 'ㅇ', 'ㄷ': 'ㄴ', 'ㅂ': 'ㅁ' };
    var LIAISON = {
        'ㄳ': ['ㄱ', 'ㅆ'], 'ㄵ': ['ㄴ', 'ㅈ'], 'ㄺ': ['ㄹ', 'ㄱ'], 'ㄻ': ['ㄹ', 'ㅁ'],
        'ㄼ': ['ㄹ', 'ㅂ'], 'ㄽ': ['ㄹ', 'ㅆ'], 'ㄾ': ['ㄹ', 'ㅌ'], 'ㄿ': ['ㄹ', 'ㅍ'],
        'ㅄ': ['ㅂ', 'ㅆ'], 'ㄶ': ['', 'ㄴ'], 'ㅀ': ['', 'ㄹ'], 'ㅎ': ['', 'ㅇ']
    };

    function has(obj, k) { return Object.prototype.hasOwnProperty.call(obj, k); }
    function among(x, list) { return list.indexOf(x) >= 0; }

    // 子音の前・語末で実際に鳴るパッチム（7つ）
    function rep(jong, nxt) {
        if (among(jong, ['ㄱ', 'ㄲ', 'ㅋ', 'ㄳ'])) return 'ㄱ';
        if (jong === 'ㄺ') return nxt === 'ㄱ' ? 'ㄹ' : 'ㄱ';
        if (among(jong, ['ㄴ', 'ㄵ', 'ㄶ'])) return 'ㄴ';
        if (among(jong, ['ㄷ', 'ㅅ', 'ㅆ', 'ㅈ', 'ㅊ', 'ㅌ', 'ㅎ'])) return 'ㄷ';
        if (among(jong, ['ㄹ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㅀ'])) return 'ㄹ';
        if (among(jong, ['ㅁ', 'ㄻ'])) return 'ㅁ';
        if (among(jong, ['ㅂ', 'ㅍ', 'ㅄ', 'ㄿ'])) return 'ㅂ';
        return jong;
    }

    function decompose(word) {
        var out = [];
        for (var i = 0; i < word.length; i++) {
            var code = word.charCodeAt(i) - 0xAC00;
            if (code >= 0 && code < 11172) {
                var cho = CHO[Math.floor(code / 588)];
                out.push({ cho: cho, jung: JUNG[Math.floor((code % 588) / 28)], jong: JONG[code % 28], orig_cho: cho });
            }
        }
        return out;
    }

    function applyRules(syl) {
        for (var i = 0; i < syl.length - 1; i++) {
            var a = syl[i], b = syl[i + 1], j = a.jong, c = b.cho, r;
            if (!j) continue;
            if (c === 'ㅇ') {
                if (j === 'ㅇ') continue;
                if (has(LIAISON, j)) {
                    a.jong = LIAISON[j][0]; b.cho = LIAISON[j][1];
                } else {
                    a.jong = ''; b.cho = j;
                    if (b.jung === 'ㅣ' && among(j, ['ㄷ', 'ㅌ'])) b.cho = j === 'ㄷ' ? 'ㅈ' : 'ㅊ';
                }
                continue;
            }
            if (c === 'ㅎ' && !among(j, ['ㄴ', 'ㄹ', 'ㅁ', 'ㅇ', 'ㄶ', 'ㅀ', 'ㅎ'])) {
                r = ({ 'ㄺ': 'ㄱ', 'ㄼ': 'ㅂ' })[j] || rep(j);
                a.jong = among(j, ['ㄺ', 'ㄼ']) ? 'ㄹ' : '';
                if (r === 'ㄱ') b.cho = 'ㅋ';
                else if (r === 'ㅂ') b.cho = 'ㅍ';
                else if (among(j, ['ㅈ', 'ㅊ']) || (among(j, ['ㄷ', 'ㅌ']) && b.jung === 'ㅣ')) b.cho = 'ㅊ';
                else b.cho = 'ㅌ';
                continue;
            }
            if (among(j, ['ㅎ', 'ㄶ', 'ㅀ'])) {
                var keep = ({ 'ㅎ': '', 'ㄶ': 'ㄴ', 'ㅀ': 'ㄹ' })[j];
                if (has(ASPIRATE, c)) { a.jong = keep; b.cho = ASPIRATE[c]; continue; }
                if (c === 'ㅅ') { a.jong = keep; b.cho = 'ㅆ'; continue; }
                if (c === 'ㄴ') {
                    a.jong = j === 'ㅀ' ? 'ㄹ' : 'ㄴ';
                    if (j === 'ㅀ') b.cho = 'ㄹ';
                    continue;
                }
            }
            r = rep(j, c);
            if (has(NASAL, r) && among(c, ['ㄴ', 'ㅁ'])) {
                r = NASAL[r];
            } else if (c === 'ㄹ') {
                if (r === 'ㄴ') r = 'ㄹ';
                else if (among(r, ['ㅁ', 'ㅇ'])) b.cho = 'ㄴ';
                else if (has(NASAL, r)) { r = NASAL[r]; b.cho = 'ㄴ'; }
            } else if (c === 'ㄴ' && r === 'ㄹ') {
                b.cho = 'ㄹ';
            }
            if (has(TENSE, c) && (has(NASAL, r) || among(j, ['ㄵ', 'ㄻ', 'ㄺ', 'ㄼ', 'ㄾ']))) b.cho = TENSE[c];
            a.jong = r;
        }
        if (syl.length) syl[syl.length - 1].jong = rep(syl[syl.length - 1].jong);
        // 의・ㅖ の読み
        syl.forEach(function (s, k) {
            if (s.jung === 'ㅢ') {
                if (s.orig_cho !== 'ㅇ') s.jung = 'ㅣ';
                else if (k === 0) { /* 語頭の 의 はそのまま */ }
                else if (k === syl.length - 1) s.jung = 'ㅔ'; // 助詞の 의
                else s.jung = 'ㅣ';
            } else if (s.jung === 'ㅖ' && s.cho !== 'ㅇ') {
                s.jung = 'ㅔ';
            }
        });
        return syl;
    }

    function toKana(word) {
        var syl = applyRules(decompose(word)), out = '', prev = null;
        syl.forEach(function (s) {
            var rows = ROW_OF[s.cho], row = rows[0];
            if (rows[1] && prev !== null && among(prev, ['', 'ㄴ', 'ㄹ', 'ㅁ', 'ㅇ'])) row = rows[1];
            var kana = TABLE[row][VOWEL[s.jung]];
            if (among(s.cho, ['ㄲ', 'ㄸ', 'ㅃ', 'ㅆ', 'ㅉ']) && !prev) kana = 'ッ' + kana;
            out += kana + FINAL_KANA[s.jong];
            prev = s.jong;
        });
        return out;
    }

    // ローマ字: 国の方式（Revised Romanization）の字を、実際の音に当てる
    var R_CHO = { 'ㄱ': 'g', 'ㄲ': 'kk', 'ㄴ': 'n', 'ㄷ': 'd', 'ㄸ': 'tt', 'ㄹ': 'r', 'ㅁ': 'm', 'ㅂ': 'b',
        'ㅃ': 'pp', 'ㅅ': 's', 'ㅆ': 'ss', 'ㅇ': '', 'ㅈ': 'j', 'ㅉ': 'jj', 'ㅊ': 'ch', 'ㅋ': 'k',
        'ㅌ': 't', 'ㅍ': 'p', 'ㅎ': 'h' };
    var R_JUNG = { 'ㅏ': 'a', 'ㅐ': 'ae', 'ㅑ': 'ya', 'ㅒ': 'yae', 'ㅓ': 'eo', 'ㅔ': 'e', 'ㅕ': 'yeo',
        'ㅖ': 'ye', 'ㅗ': 'o', 'ㅘ': 'wa', 'ㅙ': 'wae', 'ㅚ': 'oe', 'ㅛ': 'yo', 'ㅜ': 'u',
        'ㅝ': 'wo', 'ㅞ': 'we', 'ㅟ': 'wi', 'ㅠ': 'yu', 'ㅡ': 'eu', 'ㅢ': 'ui', 'ㅣ': 'i' };
    var R_JONG = { '': '', 'ㄱ': 'k', 'ㄴ': 'n', 'ㄷ': 't', 'ㄹ': 'l', 'ㅁ': 'm', 'ㅂ': 'p', 'ㅇ': 'ng' };
    var R_AFTER_STOP = { 'ㄲ': 'k', 'ㄸ': 't', 'ㅃ': 'p', 'ㅆ': 's', 'ㅉ': 'j' };

    function toRoman(word) {
        var syl = applyRules(decompose(word)), out = '', prev = null;
        syl.forEach(function (s) {
            var c = s.cho, head;
            if (c === 'ㄹ' && prev === 'ㄹ') head = 'l';
            else if (has(R_AFTER_STOP, c) && among(prev, ['ㄱ', 'ㄷ', 'ㅂ'])) head = R_AFTER_STOP[c];
            else head = R_CHO[c];
            if (!head && prev === 'ㅇ') head = '-'; // 영광을 → yeonggwang-eul
            out += head + R_JUNG[s.jung] + R_JONG[s.jong];
            prev = s.jong;
        });
        return out;
    }

    var api = { toKana: toKana, toRoman: toRoman };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else root.HangulYomi = api;
})(this);
