class CreateAlbums < ActiveRecord::Migration[5.2]
  def change
    create_table :albums do |t|
      t.string :album_artist, null: false
      t.string :album_title, null: false
      t.string :album_url, null: false
      t.string :album_cover
      t.string :album_artist_url
      t.integer :critic_rating
      t.integer :user_rating_count
      t.integer :user_rating
      t.string :release_date
      t.string :duration
      t.string :genre

      t.timestamps
    end
  end
end
