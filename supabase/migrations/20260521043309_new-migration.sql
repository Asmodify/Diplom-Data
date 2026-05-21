-- Generated SQLAlchemy Schema for PostgreSQL


CREATE TABLE facebook_posts (
	id SERIAL NOT NULL, 
	page_name TEXT NOT NULL, 
	post_id TEXT NOT NULL, 
	post_url TEXT, 
	content TEXT, 
	timestamp TIMESTAMP WITHOUT TIME ZONE, 
	likes INTEGER, 
	shares INTEGER, 
	comment_count INTEGER, 
	scraped_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (post_id)
)

;


CREATE TABLE post_images (
	id SERIAL NOT NULL, 
	post_id INTEGER NOT NULL, 
	image_url TEXT NOT NULL, 
	local_path TEXT, 
	downloaded_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(post_id) REFERENCES facebook_posts (id) ON DELETE CASCADE
)

;


CREATE TABLE post_comments (
	id SERIAL NOT NULL, 
	post_id INTEGER NOT NULL, 
	comment_id TEXT, 
	author_name TEXT, 
	author_url TEXT, 
	content TEXT, 
	timestamp TIMESTAMP WITHOUT TIME ZONE, 
	likes INTEGER, 
	reply_to_id INTEGER, 
	scraped_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(post_id) REFERENCES facebook_posts (id) ON DELETE CASCADE, 
	UNIQUE (comment_id), 
	FOREIGN KEY(reply_to_id) REFERENCES post_comments (id) ON DELETE SET NULL
)

;


CREATE TABLE analysis_results (
	id SERIAL NOT NULL, 
	post_id TEXT NOT NULL, 
	analysis_type TEXT NOT NULL, 
	result TEXT NOT NULL, 
	analyzed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)

;

-- End of generated schema
