from types import SimpleNamespace  # quick fake objects with .start/.end/.text


def seg(start, end, text):  # build a fake Whisper segment
    return SimpleNamespace(start=start, end=end, text=text)  # same fields chunk() reads


def test_no_segments_gives_no_chunks(main):  # silence / empty transcript
    assert main.chunk([]) == []  # nothing in, nothing out


def test_short_audio_is_one_chunk(main):  # under 30s stays together
    segs = [seg(0.0, 4.0, " hello "), seg(4.0, 9.5, "world")]  # 9.5 seconds total
    assert main.chunk(segs) == [(0.0, "hello world")]  # text is stripped and joined


def test_splits_every_30_seconds(main):  # long audio is cut into ~30s windows
    segs = [seg(i * 10.0, i * 10.0 + 10.0, f"s{i}") for i in range(7)]  # 0-70s in 10s pieces
    assert main.chunk(segs) == [  # 0-30, 30-60, then the 60-70 leftover
        (0.0, "s0 s1 s2"),
        (30.0, "s3 s4 s5"),
        (60.0, "s6"),
    ]


def test_chunk_starts_at_first_spoken_segment(main):  # start time = where speech begins, not 0
    segs = [seg(12.5, 20.0, "late start")]  # speech begins 12.5s in
    assert main.chunk(segs)[0][0] == 12.5  # player should jump to 12.5s


def test_custom_window(main):  # window size is configurable
    segs = [seg(0, 5, "a"), seg(5, 10, "b"), seg(10, 15, "c")]  # three 5s pieces
    assert main.chunk(segs, window=10) == [(0, "a b"), (10, "c")]  # cut at 10s
