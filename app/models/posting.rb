class Posting < ApplicationRecord
  belongs_to :user

  validates :user_id, presence: true
  validates :subject, presence: true, length: { maximum: 100 }
  validates :content, presence: true, length: { maximum: 5000 }
end
