# Telescope 数据源

## 豆瓣

### 获取一个用户的动态

`GET douban/user/life?uid={}`

`uid` 可以是字符串也可以是数字 id

Response:
```json
{
    "ok": true,
    "result": [
        {
            "time": "2019-07-30 18:30:21",
            "activity_type": "status",
            "activity": "发广播",
            "text": "只有文字",
            "images": []
        },
        {
            "time": "2019-07-30 18:12:19",
            "activity_type": "status",
            "activity": "发广播",
            "text": "",
            "images": [
                "https://img3.doubanio.com/view/status/m/public/68183360-496fc5e6b4b2d24.jpg"
            ]
        },
        {
            "time": "2019-07-30 17:36:24",
            "activity_type": "mark",
            "activity": "想看",
            "url": "https://movie.douban.com/subject/27119156/",
            "title": "怪奇物语 第三季",
            "rating": "8.9分",
            "pic": "https://img3.doubanio.com/view/photo/s_ratio_poster/public/p2558683543.jpg",
            "type": "tv"
        },
        {
            "time": "2019-07-30 17:22:32",
            "activity_type": "status",
            "activity": "发广播",
            "text": "果果",
            "images": [
                "https://img1.doubanio.com/view/status/s/public/68180447-cfa7ccde7cd6dfb.jpg",
                "https://img1.doubanio.com/view/status/s/public/68180446-37c76463ec6edeb.jpg"
            ]
        },
        {
            "time": "2019-07-30 17:09:35",
            "activity_type": "mark",
            "activity": "想读",
            "url": "https://book.douban.com/subject/33379779/",
            "title": "美国陷阱",
            "rating": "8.3分",
            "pic": "https://img3.doubanio.com/view/subject/l/public/s32305312.jpg",
            "type": "book"
        },
        {
            "time": "2019-07-30 16:53:43",
            "activity_type": "mark",
            "activity": "听过",
            "url": "https://music.douban.com/subject/26668273/",
            "title": "Blackstar",
            "rating": "9.0分",
            "pic": "https://img3.doubanio.com/view/subject/s/public/s28344624.jpg",
            "type": "music"
        }
    ]
}
```

## 微博

### 获取一个用户基本信息

`GET /weibo/user/info?uid={}`

`uid` 是用户 ID

Response:
```json
{
    "ok": true,
    "result": {
        "uid": 2214838982,
        "screen_name": "开水族馆的生物男",
        "profile_image_url": "https://tvax4.sinaimg.cn/crop.0.0.996.996.180/8403c2c6ly8fitobz5ol6j20ro0rodl3.jpg?Expires=1564462397&ssig=vyywx3untO&KID=imgbed,tva",
        "gender": "m"
    }
}
```

### 获取一个用户近期发的微博

`GET /weibo/user/blogs?uid={}`

`uid` 是用户 ID

Response:
```json
{
    "ok": true,
    "result": [
        {
            "created_at": "2018-07-25",
            "id": "4265602900396836",
            "text": "点赞的不脱发！！😭😭😭😭 {搞笑贴}",
            "source": "即刻笔记",
            "author": {
                "uid": 2504004715,
                "screen_name": "大叔神吐槽",
                "profile_image_url": "https://tva2.sinaimg.cn/crop.0.0.640.640.180/9540146bjw8eyaur8lavvj20hs0hsdgj.jpg?Expires=1564462475&ssig=fxgiHezeUK&KID=imgbed,tva",
                "gender": "m"
            },
            "pic_num": 1,
            "pics": [
                {
                    "pid": "0064e8mdly1fm7fcmnzf1g30ap06hx6q",
                    "url": "https://wx3.sinaimg.cn/orj360/0064e8mdly1fm7fcmnzf1g30ap06hx6q.gif",
                    "large_url": "https://wx3.sinaimg.cn/large/0064e8mdly1fm7fcmnzf1g30ap06hx6q.gif"
                }
            ]
        }
    ]
}
```

⚠️ `created_at` 字段为人类可读的时间，如果需要真的时间戳，调用[获取一条微博的详细信息](#获取一条微博的详细信息)接口。

### 获取一个用户赞的微博

`GET /weibo/user/likes?uid={}`

`uid` 是用户 ID

Response:
```json
{
    "ok": true,
    "result": [
        {
            "created_at": "1小时前",
            "id": "4399740223513996",
            "text": "Yeah~ 我的又一个提议被实现了  http://t.cn/AijenpMt",
            "source": "",
            "author": {
                "uid": 2813718033,
                "screen_name": "HeyJonny",
                "profile_image_url": "https://tvax2.sinaimg.cn/crop.0.0.480.480.180/a7b5ee11ly8g3i1vjbnolj20dc0dcabw.jpg?Expires=1564473584&ssig=qo2Bg1iTDV&KID=imgbed,tva",
                "gender": "m"
            }
        }
    ]
}
```

⚠️ `created_at` 为被点赞的微博的发布时间，并不是点赞的时间。

### 获取一个用户关注的用户列表

`GET /weibo/user/following?uid={}`

`uid` 是用户 ID

Response:
```json
{
    "ok": true,
    "result": [
        1952460384,
        2177245391,
        5705221157,
        1497882593
    ]
}
```

### 获取一条微博的详细信息

`GET /weibo/blog/detail?id={}`

`id` 为微博 ID

Response:
```json
{
    "ok": true,
    "result": {
        "created_at": "Sun Jul 28 12:46:46 +0800 2019",
        "id": "4399010125079253",
        "text": "我有没有抓到互联网精髓？",
        "source": "",
        "author": {
            "uid": 3467274602,
            "screen_name": "老鸡灯儿",
            "profile_image_url": "https://tvax4.sinaimg.cn/crop.0.0.690.690.180/ceaa696aly8fvmxsvkaddj20j60j6wi1.jpg?Expires=1564473691&ssig=ss1SSbNe2t&KID=imgbed,tva",
            "gender": "m"
        },
        "pic_num": 1,
        "pics": [
            {
                "pid": "ceaa696agy1g5fgqbwcy5j20yi22ohdt",
                "url": "https://wx1.sinaimg.cn/orj360/ceaa696agy1g5fgqbwcy5j20yi22ohdt.jpg",
                "large_url": "https://wx1.sinaimg.cn/large/ceaa696agy1g5fgqbwcy5j20yi22ohdt.jpg"
            }
        ]
    }
}
```

### 获取一条微博的近期评论

`GET /weibo/blog/comments?id={}`

`id` 为微博 ID

Response:
```json
{
    "ok": true,
    "result": [
        {
            "created_at": "Sun Jul 28 13:14:24 +0800 2019",
            "id": "4399017079679703",
            "text": "把我自己绕进去了妈的  网页链接",
            "source": "",
            "author": {
                "uid": 3467274602,
                "screen_name": "老鸡灯儿",
                "profile_image_url": "https://tvax4.sinaimg.cn/crop.0.0.690.690.180/ceaa696aly8fvmxsvkaddj20j60j6wi1.jpg?Expires=1564473894&ssig=oneu%2F0tIhZ&KID=imgbed,tva",
                "gender": "m"
            }
        }
    ]
}
```

### 获取一个微博的近期点赞

`GET /weibo/blog/likes?id={}`

`id` 为微博 ID

Response:
```json
{
    "ok": true,
    "result": [
        {
            "created_at": "21分钟前",
            "id": 4399764478728864,
            "text": "",
            "source": "OPPO智能手机",
            "author": {
                "uid": 6907509132,
                "screen_name": "梦死33381",
                "profile_image_url": "https://tvax1.sinaimg.cn/crop.0.0.40.40.180/007xtcFCly4fyoqi8cuu3j30140140o9.jpg?Expires=1564473951&ssig=uER201Ga%2Bq&KID=imgbed,tva",
                "gender": null
            }
        }
    ]
}
```

### 获取一个微博的近期转发

`GET /weibo/blog/reposts?id={}`

`id` 为微博 ID

Response:
```json
{
    "ok": true,
    "result": [
        {
            "created_at": "5小时前",
            "id": "4399683952970438",
            "text": "转发微博",
            "source": "iPhone客户端",
            "author": {
                "uid": 1270394743,
                "screen_name": "顾建戴",
                "profile_image_url": "https://tvax4.sinaimg.cn/default/images/default_avatar_male_180.gif?Expires=1564474070&ssig=7DC7ttL2Se&KID=imgbed,tva",
                "gender": "m"
            }
        }
    ]
}
```