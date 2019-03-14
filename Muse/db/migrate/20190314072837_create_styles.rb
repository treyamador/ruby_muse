class CreateStyles < ActiveRecord::Migration[5.2]
  def change
    create_table :styles do |t|
      t.string :style
      t.references :album, foreign_key: true

      t.timestamps
    end
  end
end
