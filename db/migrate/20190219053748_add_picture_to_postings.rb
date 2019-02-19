class AddPictureToPostings < ActiveRecord::Migration[5.0]
  def change
    add_column :postings, :picture, :string
  end
end
